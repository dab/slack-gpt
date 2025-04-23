#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
# Import setup_logging from the new config module
from app.utils.logging_config import setup_logging

# Call logging setup immediately after imports
setup_logging()

# Get a logger for this module AFTER setup
logger = logging.getLogger(__name__)

# Log application start AFTER setup is called
logger.info("SlackGPT application starting...")

# Need these imports at the top of app/main.py
# import httpx
# from urllib.parse import parse_qs
# import json

# Remove os and dotenv imports, they are handled in config.py
# import os
# from dotenv import load_dotenv

# Import config variables first
from app.utils import config

from slack_bolt.async_app import AsyncApp
# Add OAuth related imports
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings
# Reverted paths for v1.18 -> Corrected paths using slack_sdk for v1.18
from slack_sdk.oauth.installation_store.file import FileInstallationStore
from slack_sdk.oauth.state_store.file import FileOAuthStateStore

# Load environment variables from .env file
# load_dotenv() # This is now done in app.utils.config

# Configure logging - REMOVED - Now handled by setup_logging()
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
# )
# logger = logging.getLogger(__name__) # Moved up after setup_logging

# Try to initialize the Slack Bolt app, but catch authentication errors
try:
    # Define scopes required by the application
    bot_scopes = ["commands", "chat:write", "app_mentions:read"]

    # Configure OAuth settings explicitly
    oauth_settings = AsyncOAuthSettings(
        client_id=config.SLACK_CLIENT_ID,
        client_secret=config.SLACK_CLIENT_SECRET,
        scopes=bot_scopes,
        installation_store=FileInstallationStore(base_dir="/app/data/installation"),
        state_store=FileOAuthStateStore(expiration_seconds=600, base_dir="/app/data/state"),
    )

    app = AsyncApp(
        # Initialize using signing secret and explicit OAuth settings
        signing_secret=config.SLACK_SIGNING_SECRET,
        oauth_settings=oauth_settings,
    )

    # Simple health check endpoint
    @app.command("/health")
    async def health_check(ack, respond):
        """
        Health check command to verify the bot is running.
        This is for testing purposes only.
        """
        await ack()
        await respond("SlackGPT bot is healthy and running!")

    # Import and register /ask command handler
    from app.handlers.ask_command import handle_ask_command
    @app.command("/ask")
    async def ask_command_handler(ack, command, respond, logger):
        await handle_ask_command(ack, command, respond, logger)

    # Import and register /help command handler
    from app.handlers.help_command import handle_help_command
    @app.command("/help")
    async def help_command_handler(ack, command, logger):
        await handle_help_command(ack, command, logger)

    # Error handler for global app errors
    @app.error
    async def global_error_handler(error, body, logger):
        """
        Global error handler for the Slack Bolt app (async).
        """
        logger.exception(f"Error: {error} | Body: {body}")

except Exception as e:
    # If App init fails, log critical error and potentially exit or use a minimal error app
    logger.critical(f"CRITICAL: Failed to initialize Slack Bolt App: {e}", exc_info=True)
    # Define a minimal ASGI error app
    async def critical_error_app(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 500, 'headers': [(b'content-type', b'text/plain')]})
        await send({'type': 'http.response.body', 'body': b'Application failed to initialize. Check server logs.'})
    app = critical_error_app # Assign the error handler app
    # logger.info("Initializing Fallback ASGI App for OAuth.")
    # # Fallback ASGI app specifically for OAuth callback
    # async def oauth_fallback_app(scope, receive, send):
    #     # ... (Keep previous fallback code commented out or remove) ...
    # app = oauth_fallback_app # Assign the error handler app

# Run the app using Socket Mode if running as a script
if __name__ == "__main__":
    # For local development with Socket Mode
    if isinstance(app, AsyncApp):
        # Use PORT from config module
        app.start(port=config.PORT)
    else:
        logger.info("Running dummy app for Docker verification")
        # Simple HTTP server
        import uvicorn
        # Use PORT from config module
        uvicorn.run(app, host="0.0.0.0", port=config.PORT)

# Always create the ASGI adapter at module level for Uvicorn
from slack_bolt.adapter.asgi.async_handler import AsyncSlackRequestHandler
api = AsyncSlackRequestHandler(app)
