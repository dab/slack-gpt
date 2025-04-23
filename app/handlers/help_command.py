import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def handle_help_command(ack, command: Dict[str, Any]):
    """
    Handler for the /help slash command. Returns a formatted help message using Slack Block Kit.
    """
    user_id = command.get('user_id', 'unknown')
    logger.info(f"/help command received | user_id={user_id}")
    try:
        help_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Welcome to the Slack GPT Bot!* :robot_face:\n\n"
                        "This bot helps you get instant answers and assistance using AI.\n\n"
                        "*Available Commands:*\n"
                        "• `/ask <question>` — Ask any question and get an AI-powered answer.\n"
                        "• `/help` — Show this help message.\n\n"
                        "_Tip: Use `/ask` to get started!_"
                    )
                }
            }
        ]
        await ack(blocks=help_blocks)
    except Exception as e:
        logger.error(f"Error in /help handler: {e}")
        await ack(text="Sorry, something went wrong displaying the help message.") 