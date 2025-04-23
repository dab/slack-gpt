import logging
import sys
import os

def setup_logging():
    """Configures the root logger."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Use basicConfig for simplicity, directing output to stdout
    logging.basicConfig(
        level=log_level,
        format=log_format,
        stream=sys.stdout # Ensure logs go to stdout for Docker
    )

    # Optionally, get the root logger and log a message
    logger = logging.getLogger()
    logger.info(f"Logging configured with level: {log_level}")

# Example of how to get a logger in other modules:
# import logging
# logger = logging.getLogger(__name__) 