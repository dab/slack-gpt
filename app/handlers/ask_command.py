import hashlib
import re
import logging
from app.services.redis_service import RedisService
from app.services.knowledge_base import KnowledgeBaseService
from app.services.openai_service import OpenAIService
from app.utils import config

# Helper to format answers as Slack Block Kit

def format_block_kit(answer_text: str):
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": answer_text
            }
        }
    ]

# Handler for /ask command
async def handle_ask_command(ack, command, respond, logger=None):
    if logger is None:
        logger = logging.getLogger(__name__)
    redis_service = RedisService()
    kb_service = KnowledgeBaseService(config.PDF_DATA_DIR)
    openai_service = OpenAIService()

    await ack()  # Immediate ack

    question = command.get('text', '').strip()
    if not question:
        usage = "*Usage:* `/ask <your question>`\n_Ask a question and I'll try to answer using my knowledge base and OpenAI._"
        await respond(blocks=format_block_kit(usage))
        return

    # Normalize question
    normalized = re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', question.lower())).strip()
    cache_key = hashlib.sha256(normalized.encode()).hexdigest()

    cached_answer = await redis_service.get_value(cache_key)
    if cached_answer:
        await respond(blocks=format_block_kit(cached_answer))
        logger.info(f"Cache hit for /ask: {question}")
        return
    else:
        logger.info(f"Cache miss for /ask: {question}")

    context = await kb_service.find_relevant_context(question)
    answer = await openai_service.get_answer(question, context)
    if answer:
        await redis_service.set_value(cache_key, answer, ttl_seconds=86400)
        await respond(blocks=format_block_kit(answer))
        logger.info(f"Answer sent for /ask: {question}")
    else:
        await respond(blocks=format_block_kit("Sorry, I couldn't find an answer to your question."))
        logger.warning(f"No answer found for /ask: {question}") 