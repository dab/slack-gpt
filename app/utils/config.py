import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This is useful for local development.
load_dotenv()

# --- Slack Configuration ---
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
# Optional: SLACK_APP_TOKEN for Socket Mode (if used)
# SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID") # Added for OAuth
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET") # Added for OAuth
SLACK_STATE_SECRET = os.getenv("SLACK_STATE_SECRET", "my-default-state-secret") # Added for OAuth state verification

# --- OpenAI Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Redis Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# --- Data Configuration ---
PDF_DATA_DIR = os.getenv("PDF_DATA_DIR", "/app/data/pdfs") # Default to a path within the container

# --- Application Configuration ---
APP_ENV = os.getenv("APP_ENV", "development") # e.g., development, production
PORT = int(os.getenv("PORT", 3000))

# --- Knowledge Base / OpenAI Context Configuration ---
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", 7000))

# Simple validation to ensure critical variables are set
required_vars = [
    "SLACK_BOT_TOKEN", # Temporarily commented out for initial install -> Uncommented
    "SLACK_SIGNING_SECRET",
    "OPENAI_API_KEY",
    "SLACK_CLIENT_ID", # Added for OAuth
    "SLACK_CLIENT_SECRET", # Added for OAuth
    # SLACK_STATE_SECRET is optional, has default
    # Add other mandatory variables here if needed
]

missing_vars = [var for var in required_vars if not globals().get(var)]

if missing_vars:
    raise ValueError(f"Missing critical environment variables: {', '.join(missing_vars)}")

print(f"Configuration loaded for environment: {APP_ENV}")
# Optionally, print non-sensitive config for debugging (be careful!)
# print(f"Redis Host: {REDIS_HOST}")
# print(f"PDF Data Dir: {PDF_DATA_DIR}") 