"""OpenAI LLM Client with error handling."""

import logging
import json
from typing import Any
from openai import AsyncOpenAI, APIError, AuthenticationError, RateLimitError
from openai.types.chat import ChatCompletion
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

    def _build_openai_messages(
            self,
            messages: list[AgentMessage],
            system_message: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Convert AgentMessage list to OpenAI format, handling tool_call_data.

        Args:
            messages: Message history (AgentMessage DTOs)
            system_message: System message (optional)

        Returns:
            List of messages in OpenAI format
        """
        openai_messages = []

        if system_message:
            openai_messages.append({
                "role": "system",
                "content": system_message
            })

        for msg in messages:
            # Check if message has tool call data
            if msg.tool_call_data:
                # Assistant message with tool_calls
                if "tool_calls" in msg.tool_call_data:
                    openai_messages.append({
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": msg.tool_call_data["tool_calls"]
                    })

                    # Add tool result messages
                    if "tool_results" in msg.tool_call_data:
                        for result in msg.tool_call_data["tool_results"]:
                            openai_messages.append({
                                "role": "tool",
                                "tool_call_id": result["tool_call_id"],
                                "name": result["name"],
                                "content": json.dumps(result["result"])
                            })

                    # Add final assistant response after tools
                    if msg.content:
                        openai_messages.append({
                            "role": "assistant",
                            "content": msg.content
                        })
            else:
                # Regular message without tools
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return openai_messages

    async def chat_completion(
            self,
            messages: list[AgentMessage],
            system_message: str | None = None,
            tools: list[dict[str, Any]] | None = None
    ) -> ChatCompletion:
        """
        Call OpenAI API with proper error handling.

        Args:
            messages: Message history (AgentMessage DTOs)
            system_message: System message (optional)
            tools: OpenAI function calling schemas (optional)

        Returns:
            Full ChatCompletion response object

        Raises:
            LLMAuthenticationError: Invalid API key
            LLMRateLimitError: Rate limit exceeded
            LLMContextLengthError: Context length exceeded
            LLMError: Other LLM errors
        """
        # Convert AgentMessage to OpenAI format
        openai_messages = self._build_openai_messages(messages, system_message)

        try:
            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }

            # Add tools if provided
            if tools:
                request_params["tools"] = tools

            response = await self.client.chat.completions.create(**request_params)

            return response

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
