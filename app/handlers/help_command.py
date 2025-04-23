from typing import Any, Dict


async def handle_help_command(ack, command: Dict[str, Any], logger):
    """
    Handler for the /help slash command. Returns a formatted help message using Slack Block Kit.
    """
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