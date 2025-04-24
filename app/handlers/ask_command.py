import hashlib
import re
import logging
import json
from slack_bolt.async_app import AsyncAck, AsyncRespond

# Use relative imports because the app root is the Python path in Docker
from app.services.redis_service import RedisService
from app.services.knowledge_base import KnowledgeBaseService
from app.services.openai_service import OpenAIService
from app.utils import config
import datetime

logger = logging.getLogger(__name__)

# Helper to format answers as Slack Block Kit

def format_block_kit(answer_text: str, question_text: str = None):
    blocks = []
    if question_text:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":question: *You asked:*\n>{question_text}"
            }
        })
        blocks.append({"type": "divider"})
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": answer_text
        }
    })
    return blocks

# --- Block Kit error messages ---
generic_error_blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": ":warning: Sorry, something went wrong while processing your request. Please try again later."}}
]
openai_error_blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": ":robot_face: Sorry, I'm having trouble connecting to my brain right now. Please try again soon!"}}
]
not_found_blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": ":mag: I couldn't find a specific answer to your question, but you can try rephrasing or asking something else!"}}
]

# Handler for /ask command
async def handle_ask_command(ack, command, respond):
    user_id = command.get('user_id', 'unknown')
    question = command.get('text', '').strip()
    timestamp = datetime.datetime.utcnow().isoformat()

    # Normalize question
    normalized = re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', question.lower())).strip()
    cache_key = hashlib.sha256(normalized.encode()).hexdigest()

    logger.info(f"/ask command received | user_id={user_id} | timestamp={timestamp} | request_id={cache_key}")
    redis_service = RedisService()
    kb_service = KnowledgeBaseService(config.PDF_DATA_DIR)
    openai_service = OpenAIService()

    await ack()  # Immediate ack

    if not question:
        usage = "*Usage:* `/ask <your question>`\n_Ask a question and I'll try to answer using my knowledge base and OpenAI._"
        await respond(blocks=format_block_kit(usage))
        return

    # --- Redis get_value with error handling ---
    try:
        cached_answer = await redis_service.get_value(cache_key)
    except Exception as e:
        logger.exception(f"Redis get_value error for /ask: {question}")
        cached_answer = None  # Proceed as cache miss

    if cached_answer:
        await respond(blocks=format_block_kit(cached_answer, question_text=question))
        logger.info(f"Cache hit for key: {cache_key}")
        return
    else:
        logger.info(f"Cache miss for key: {cache_key}")

    # --- KnowledgeBaseService with error handling ---
    try:
        context = await kb_service.find_relevant_context(question, request_id=cache_key)
    except Exception as e:
        logger.exception(f"KnowledgeBaseService error for /ask: {question}")
        await respond(blocks=generic_error_blocks)
        return

    # --- OpenAIService with error handling ---
    try:
        answer = await openai_service.get_answer(question, context, request_id=cache_key)
    except Exception as e:
        logger.exception(f"OpenAIService error for /ask: {question}")
        await respond(blocks=openai_error_blocks)
        return

    # --- Not found or no answer logic ---
    if answer is None or (isinstance(answer, str) and not answer.strip()):
        await respond(blocks=not_found_blocks)
        logger.warning(f"No answer found for /ask: {question} | request_id={cache_key}")
        logger.info(f"Sending answer (source: not_found) | request_id={cache_key}")
        return

    # --- Redis set_value with error handling ---
    try:
        await redis_service.set_value(cache_key, answer, ttl_seconds=86400)
    except Exception as e:
        logger.exception(f"Redis set_value error for /ask: {question}")
        # Do not block sending the answer to the user

    await respond(blocks=format_block_kit(answer, question_text=question))
    # Check if the answer came from cache or OpenAI
    source = "cache" if cached_answer else "openai"
    logger.info(f"Sending answer (source: {source}) | request_id={cache_key}") 