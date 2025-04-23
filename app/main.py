#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

from dotenv import load_dotenv
from slack_bolt import App

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize the Slack Bolt app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


# Simple health check endpoint
@app.command("/health")
def health_check(ack, respond):
    """
    Health check command to verify the bot is running.
    This is for testing purposes only.
    """
    ack()
    respond("SlackGPT bot is healthy and running!")


# Error handler for global app errors
@app.error
def global_error_handler(error, logger):
    """
    Global error handler for the Slack Bolt app.
    """
    logger.exception(f"Error: {error}")


# Run the app using Socket Mode if running as a script
if __name__ == "__main__":
    # For local development with Socket Mode
    app.start(port=int(os.environ.get("PORT", 3000)))
else:
    # For production with HTTP mode and ASGI
    from slack_bolt.adapter.asgi import ASGIAdapter

    api = ASGIAdapter(app)
