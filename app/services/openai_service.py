"""
Service for interacting with the OpenAI API.
"""

import os
import logging
from openai import AsyncOpenAI, APIError # Removed unused import 'openai'
from typing import Optional

# Basic logging configuration (ensure this is set up elsewhere properly in a real app)
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Handles interactions with the OpenAI API for generating answers.
    """
    def __init__(self):
        """Initializes the asynchronous OpenAI client."""
        self.client = AsyncOpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        logging.info("OpenAI service initialized.") # Corrected spacing

    async def get_answer(self, question: str, context: str) -> Optional[str]:
        """Gets an answer from the OpenAI model based on the question and context."""
        if not self.client:
            logging.error("OpenAI client not initialized.")
            return None

        messages = [
            {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ]

        try:
            logging.info(f"Calling OpenAI API with model gpt-4o-mini. Question: {question[:70]}...") # Shortened log message
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            answer = response.choices[0].message.content
            logging.info("Successfully received answer from OpenAI API.")
            return answer
        except APIError as e:
            logging.error(f"OpenAI API error occurred: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during OpenAI API call: {e}")
            return None 