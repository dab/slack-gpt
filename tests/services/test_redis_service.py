# Use AsyncMock directly for clearer async mocking
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
import redis.asyncio as redis
from redis.exceptions import RedisError

# Module to be tested
from app.services.redis_service import RedisService

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def mock_redis_client():
    """Fixture to create a mock async Redis client."""
    # Create the base mock
    mock = AsyncMock(spec=redis.Redis)
    # Ensure the methods we call are also AsyncMocks
    mock.get = AsyncMock()
    mock.setex = AsyncMock()
    mock.close = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def redis_service(mock_redis_client):
    """Fixture to create a RedisService instance with a mocked client."""
    with patch(
        "redis.asyncio.from_url", return_value=mock_redis_client
    ) as _:
        service = RedisService()
        assert service.redis_client == mock_redis_client
        yield service
        # Cleanup: Ensure close is called on the mock if the service still has it
        if service.redis_client:
            await service.close()
            # Use assert_awaited() for methods without args if needed,
            # or assert_awaited_once_with for methods with args.
            mock_redis_client.close.assert_awaited_once()


# --- Test Cases ---


async def test_redis_service_init_success(mock_redis_client):
    """Test successful initialization of RedisService."""
    with patch(
        "redis.asyncio.from_url", return_value=mock_redis_client
    ) as _:
        service = RedisService()
        assert service.redis_client is not None
        # Explicitly await close on the mock returned by the patched from_url
        await service.redis_client.close()
        # Assert that the close mock *within* the main mock was called
        service.redis_client.close.assert_awaited_once()


async def test_redis_service_init_failure():
    """Test initialization failure of RedisService."""
    error_message = "Connection failed"
    with patch(
        "redis.asyncio.from_url", side_effect=RedisError(error_message)
    ) as mock_from_url:
        with patch("app.services.redis_service.logger.exception") as mock_log_exception:
            service = RedisService()
            assert service.redis_client is None
            mock_from_url.assert_called_once()
            mock_log_exception.assert_called_once_with(
                f"Failed to initialize Redis client: {error_message}"
            )


async def test_get_value_success(redis_service, mock_redis_client):
    """Test successfully getting a value."""
    # Set the return value of the async get mock
    mock_redis_client.get.return_value = "test_value"
    result = await redis_service.get_value("test_key")
    assert result == "test_value"
    # Assert the async get mock was awaited correctly
    mock_redis_client.get.assert_awaited_once_with("test_key")


async def test_get_value_not_found(redis_service, mock_redis_client):
    """Test getting a value when the key is not found."""
    mock_redis_client.get.return_value = None
    result = await redis_service.get_value("nonexistent_key")
    assert result is None
    mock_redis_client.get.assert_awaited_once_with("nonexistent_key")


async def test_get_value_redis_error(redis_service, mock_redis_client):
    """Test handling RedisError during get_value."""
    # Set the side effect on the async get mock
    mock_redis_client.get.side_effect = RedisError("GET failed")
    with patch("app.services.redis_service.logger.exception") as mock_log_exception:
        result = await redis_service.get_value("error_key")
        assert result is None
        mock_redis_client.get.assert_awaited_once_with("error_key")
        mock_log_exception.assert_called_once()
        assert "Redis error getting value" in mock_log_exception.call_args[0][0]


async def test_get_value_client_not_initialized():
    """Test get_value when the client failed to initialize."""
    # Simulate init failure
    with patch("redis.asyncio.from_url", side_effect=RedisError("init failed")):
        service = RedisService()
        assert service.redis_client is None
        with patch("app.services.redis_service.logger.error") as mock_log_error:
            result = await service.get_value("any_key")
            assert result is None
            mock_log_error.assert_called_once_with(
                "Redis client not initialized. Cannot get value."
            )


async def test_set_value_success(redis_service, mock_redis_client):
    """Test successfully setting a value with TTL."""
    # Set return value for setex (usually None, but needs to be awaitable)
    mock_redis_client.setex.return_value = (
        None  # AsyncMock automatically makes this awaitable
    )
    await redis_service.set_value("set_key", "set_value", 3600)
    mock_redis_client.setex.assert_awaited_once_with("set_key", 3600, "set_value")


async def test_set_value_redis_error(redis_service, mock_redis_client):
    """Test handling RedisError during set_value."""
    mock_redis_client.setex.side_effect = RedisError("SET failed")
    with patch("app.services.redis_service.logger.exception") as mock_log_exception:
        await redis_service.set_value("error_key", "error_value", 60)
        mock_redis_client.setex.assert_awaited_once_with("error_key", 60, "error_value")
        mock_log_exception.assert_called_once()
        assert "Redis error setting value" in mock_log_exception.call_args[0][0]


async def test_set_value_client_not_initialized():
    """Test set_value when the client failed to initialize."""
    # Simulate init failure
    with patch("redis.asyncio.from_url", side_effect=RedisError("init failed")):
        service = RedisService()
        assert service.redis_client is None
        with patch("app.services.redis_service.logger.error") as mock_log_error:
            await service.set_value("any_key", "any_value", 60)
            mock_log_error.assert_called_once_with(
                "Redis client not initialized. Cannot set value."
            )


async def test_close_success(redis_service, mock_redis_client):
    """Test that close is called on the underlying client."""
    # The close check is handled in the fixture teardown
    pass


async def test_close_client_already_none():
    """Test close does nothing if client is None."""
    with patch("redis.asyncio.from_url", side_effect=RedisError("init failed")):
        service = RedisService()
        assert service.redis_client is None
        # Directly call close and ensure no error/mock calls happen
        with patch.object(service, "redis_client", new=None) as _:
            await service.close()
            # Check close was not awaited on the (now None) client attribute
            # (No direct assertion needed, just checking no error)
