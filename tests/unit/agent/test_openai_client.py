"""Tests for OpenAI LLM Client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from openai import AuthenticationError, RateLimitError, APIError

from src.agent.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMContextLengthError,
    LLMError
)


@pytest.mark.unit
class TestOpenAIClientSuccess:
    """Tests for successful OpenAI API calls."""

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, openai_client, sample_messages):
        """Test successful chat completion."""
        # Mock successful OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I'm doing great, thanks!"

        with patch.object(
            openai_client.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await openai_client.chat_completion(sample_messages)

            assert result == "I'm doing great, thanks!"

    @pytest.mark.asyncio
    async def test_chat_completion_with_system_message(self, openai_client, sample_messages):
        """Test chat completion with system message."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        with patch.object(
            openai_client.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_create:
            await openai_client.chat_completion(
                sample_messages,
                system_message="You are a helpful assistant."
            )

            # Verify system message was included
            call_args = mock_create.call_args
            messages = call_args.kwargs['messages']

            assert messages[0]['role'] == 'system'
            assert messages[0]['content'] == "You are a helpful assistant."
            assert len(messages) == 4  # system + 3 sample messages

    @pytest.mark.asyncio
    async def test_message_format_conversion(self, openai_client, sample_messages):
        """Test AgentMessage to OpenAI format conversion."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        with patch.object(
            openai_client.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_create:
            await openai_client.chat_completion(sample_messages)

            # Verify message format conversion
            call_args = mock_create.call_args
            messages = call_args.kwargs['messages']

            assert messages[0] == {'role': 'user', 'content': 'Hello'}
            assert messages[1] == {'role': 'assistant', 'content': 'Hi there!'}
            assert messages[2] == {'role': 'user', 'content': 'How are you?'}


@pytest.mark.unit
class TestOpenAIClientErrors:
    """Tests for OpenAI API error handling."""

    @pytest.mark.asyncio
    async def test_authentication_error(self, openai_client, sample_messages):
        """Test handling of authentication error (invalid API key)."""
        with patch.object(
            openai_client.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            side_effect=AuthenticationError(
                message="Invalid API key",
                response=MagicMock(status_code=401),
                body={}
            )
        ):
            with pytest.raises(LLMAuthenticationError) as exc_info:
                await openai_client.chat_completion(sample_messages)

            assert "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, openai_client, sample_messages):
        """Test handling of rate limit error."""
        with patch.object(
            openai_client.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body={}
            )
        ):
            with pytest.raises(LLMRateLimitError) as exc_info:
                await openai_client.chat_completion(sample_messages)

            assert "rate limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_context_length_error(self, openai_client, sample_messages):
        """Test handling of context length exceeded error."""
        with patch.object(
            openai_client.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            side_effect=APIError(
                message="maximum context length exceeded",
                request=MagicMock(),
                body={}
            )
        ):
            with pytest.raises(LLMContextLengthError) as exc_info:
                await openai_client.chat_completion(sample_messages)

            assert "too long" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generic_api_error(self, openai_client, sample_messages):
        """Test handling of generic API error."""
        with patch.object(
            openai_client.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            side_effect=APIError(
                message="Server error",
                request=MagicMock(),
                body={}
            )
        ):
            with pytest.raises(LLMError) as exc_info:
                await openai_client.chat_completion(sample_messages)

            assert "OpenAI API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unexpected_error(self, openai_client, sample_messages):
        """Test handling of unexpected error."""
        with patch.object(
            openai_client.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            side_effect=Exception("Unexpected error")
        ):
            with pytest.raises(LLMError) as exc_info:
                await openai_client.chat_completion(sample_messages)

            assert "Unexpected LLM error" in str(exc_info.value)


@pytest.mark.unit
class TestOpenAIClientConfiguration:
    """Tests for OpenAI client configuration."""

    def test_client_initialization(self, openai_client):
        """Test that client is initialized with correct settings."""
        assert openai_client.model == "gpt-4o-mini"
        assert openai_client.temperature == 0.7
        assert openai_client.max_tokens == 2000

    @pytest.mark.asyncio
    async def test_api_call_parameters(self, openai_client, sample_messages):
        """Test that API is called with correct parameters."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"

        with patch.object(
            openai_client.client.chat.completions,
            'create',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_create:
            await openai_client.chat_completion(sample_messages)

            # Verify API call parameters
            call_args = mock_create.call_args
            assert call_args.kwargs['model'] == "gpt-4o-mini"
            assert call_args.kwargs['temperature'] == 0.7
            assert call_args.kwargs['max_tokens'] == 2000