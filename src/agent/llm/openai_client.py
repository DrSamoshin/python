"""OpenAI LLM Client with error handling."""

import logging
from openai import AsyncOpenAI, APIError, AuthenticationError, RateLimitError
from src.agent.configs import settings
from src.agent.dto import AgentMessage
from src.agent.exceptions import (
    LLMError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMContextLengthError
)

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API client with comprehensive error handling."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens

    async def chat_completion(
            self,
            messages: list[AgentMessage],
            system_message: str | None = None
    ) -> str:
        """
        Call OpenAI API with proper error handling.

        Args:
            messages: Message history (AgentMessage DTOs)
            system_message: System message (optional)

        Returns:
            Generated response content

        Raises:
            LLMAuthenticationError: Invalid API key
            LLMRateLimitError: Rate limit exceeded
            LLMContextLengthError: Context length exceeded
            LLMError: Other LLM errors
        """
        # Convert AgentMessage to OpenAI format
        openai_messages = []

        if system_message:
            openai_messages.append({
                "role": "system",
                "content": system_message
            })

        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content

        except AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            raise LLMAuthenticationError(
                "OpenAI API key is invalid. Please check AGENT_OPENAI_API_KEY in .env"
            ) from e

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise LLMRateLimitError(
                "OpenAI rate limit exceeded. Please try again later."
            ) from e

        except APIError as e:
            # Check for context length error
            error_str = str(e).lower()
            if "context_length_exceeded" in error_str or "maximum context length" in error_str:
                logger.error(f"OpenAI context length exceeded: {e}")
                raise LLMContextLengthError(
                    "Message history too long. Please start a new chat."
                ) from e

            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"OpenAI API error: {str(e)}") from e

        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise LLMError(f"Unexpected LLM error: {str(e)}") from e
