import logging
import os
from typing import Union

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisService:
    """Service class for interacting with Redis."""

    def __init__(self):
        """Initializes the RedisService and the Redis client.

        Reads connection details from environment variables.
        Handles potential connection issues during initialization.
        """
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_password = os.getenv("REDIS_PASSWORD", None)

        redis_url = f"redis://{':'+redis_password+'@' if redis_password else ''}{redis_host}:{redis_port}/0"

        logger.info(
            f"Initializing Redis client with URL: redis://{'<password>@' if redis_password else ''}{redis_host}:{redis_port}/0"
        )

        try:
            # Note: Connection is established lazily, not immediately here.
            # We'll rely on later commands to surface actual connection errors.
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,  # Decode responses from bytes to strings
                socket_connect_timeout=5,  # Set a timeout for connection attempts
                # Additional options like retry logic could be added here.
            )
            logger.info("Redis client initialized.")
        except Exception as e:
            logger.exception(f"Failed to initialize Redis client: {e}")
            self.redis_client = None  # Ensure client is None if init fails

    async def get_value(self, key: str) -> Union[str, None]:
        """Gets a value from Redis for the given key.

        Args:
            key: The key to retrieve.

        Returns:
            The value as a string if the key exists, otherwise None.
            Returns None on Redis connection errors.
        """
        if not self.redis_client:
            logger.error("Redis client not initialized. Cannot get value.")
            return None
        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                logger.debug(f"Cache miss for key: {key}")
                return None
        except redis.RedisError as e:
            logger.exception(f"Redis error getting value for key '{key}': {e}")
            return None
        except Exception as e:
            logger.exception(
                f"Unexpected error getting value for key '{key}': {e}"
            )
            # return None # Already returning None within this block

        # Explicitly return None if no value was found or an error occurred
        return None

    async def set_value(self, key: str, value: str, ttl_seconds: int):
        """Sets a value in Redis with a specific time-to-live (TTL).

        Args:
            key: The key to set.
            value: The value to store.
            ttl_seconds: The time-to-live in seconds.
        """
        if not self.redis_client:
            logger.error("Redis client not initialized. Cannot set value.")
            return
        try:
            await self.redis_client.setex(key, ttl_seconds, value)
            logger.debug(f"Cache set for key: {key} with TTL: {ttl_seconds}s")
        except redis.RedisError as e:
            logger.exception(f"Redis error setting value for key '{key}': {e}")
        except Exception as e:
            logger.exception(f"Unexpected error setting value for key '{key}': {e}")

    async def close(self):
        """Closes the Redis client connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis client connection closed.")
