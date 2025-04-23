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

from slack_bolt import App
# Add OAuth related imports
from slack_bolt.oauth.oauth_settings import OAuthSettings
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
    oauth_settings = OAuthSettings(
        client_id=config.SLACK_CLIENT_ID,
        client_secret=config.SLACK_CLIENT_SECRET,
        # state_secret=config.SLACK_STATE_SECRET, # Removed: Not a valid arg in v1.18.0; handled by state_store
        scopes=bot_scopes,
        # Use default file stores (paths relative to execution dir: /app inside container)
        # Corrected paths for base_dir to match volume mount
        installation_store=FileInstallationStore(base_dir="/app/data/installation"),
        state_store=FileOAuthStateStore(expiration_seconds=600, base_dir="/app/data/state"),
        # Optional: Define specific install path, redirect URI path etc. if needed
        # install_path="/slack/install",
        # redirect_uri_path="/slack/oauth_redirect",
    )

    app = App(
        # Initialize using signing secret and explicit OAuth settings
        # token argument is ignored when oauth_settings are provided
        signing_secret=config.SLACK_SIGNING_SECRET,
        oauth_settings=oauth_settings,
        # token=config.SLACK_BOT_TOKEN, # Not needed here
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
    if isinstance(app, App):
        # Use PORT from config module
        app.start(port=config.PORT)
    else:
        logger.info("Running dummy app for Docker verification")
        # Simple HTTP server
        import uvicorn
        # Use PORT from config module
        uvicorn.run(app, host="0.0.0.0", port=config.PORT)
else:
    # For production with HTTP mode and ASGI
    # Use the ASGIAdapter/SlackRequestHandler to make the Bolt App compatible with Uvicorn
    from slack_bolt.adapter.asgi import SlackRequestHandler # Use SlackRequestHandler for slack-bolt v1.18
    api = SlackRequestHandler(app)
