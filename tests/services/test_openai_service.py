import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

# Assuming the service class is in app.services.openai_service
# Adjust the import path if necessary based on your project structure
from app.services.openai_service import OpenAIService

# Mock the os.getenv call for OPENAI_API_KEY
@pytest.fixture(autouse=True)
def mock_getenv():
    with patch('os.getenv') as mock_get:
        mock_get.return_value = "fake-api-key"
        yield mock_get

@pytest_asyncio.fixture
async def openai_service():
    """Fixture to create an instance of OpenAIService."""
    service = OpenAIService()
    yield service

class TestOpenAIService:
    """Unit tests for the OpenAIService class."""

    @pytest.mark.asyncio
    async def test_get_answer_success(self, openai_service):
        """Tests successful retrieval of an answer from the API."""
        mock_completion_response = AsyncMock()
        mock_completion_response.choices = [
            AsyncMock(message=AsyncMock(content="This is a test answer."))
        ]

        with patch.object(openai_service.client.chat.completions, 'create', new=AsyncMock(return_value=mock_completion_response)) as mock_create:
            question = "What is the capital of France?"
            context = "Paris is the capital of France."
            answer = await openai_service.get_answer(question, context)

            mock_create.assert_called_once_with(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
                ],
                max_tokens=500,
                temperature=0.7,
            )
            assert answer == "This is a test answer."

    @pytest.mark.asyncio
    async def test_get_answer_api_error(self, openai_service):
        """Tests handling of an OpenAI API error."""
        from openai import APIError
        from unittest.mock import MagicMock

        # Create a mock request object
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url = "https://api.openai.com/v1/chat/completions"

        # Instantiate APIError with the message, mock request, and an empty body dictionary
        with patch.object(openai_service.client.chat.completions, 'create', new=AsyncMock(side_effect=APIError("Rate limit exceeded", request=mock_request, body={}))):
            question = "What is the capital of France?"
            context = "Paris is the capital of France."
            answer = await openai_service.get_answer(question, context)

            assert answer is None 

    @pytest.mark.asyncio
    async def test_get_answer_generic_exception(self, openai_service):
        """Tests handling of a generic exception during API call."""
        with patch.object(openai_service.client.chat.completions, 'create', new=AsyncMock(side_effect=Exception("unexpected"))), \
             patch('logging.error') as mock_log_error:
            question = "What is the capital of Mars?"
            context = "Mars has no capital."
            answer = await openai_service.get_answer(question, context)
            assert answer is None
            mock_log_error.assert_called_once()
            assert "An unexpected error occurred" in mock_log_error.call_args[0][0] 