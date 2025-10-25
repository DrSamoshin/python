"""Tests for AgentOrchestrator."""

import pytest
from unittest.mock import AsyncMock, patch

from src.agent.dto import AgentMessage, AgentRequest, AgentResponse
from src.agent.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMContextLengthError,
    LLMError
)


@pytest.mark.unit
class TestAgentOrchestratorSuccess:
    """Tests for successful AgentOrchestrator processing."""

    @pytest.mark.asyncio
    async def test_process_success(self, orchestrator, sample_request):
        """Test successful message processing."""
        # Mock successful LLM response
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I'm doing great, thanks for asking!"
        mock_response.choices[0].message.tool_calls = None

        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            response = await orchestrator.process(sample_request)

            assert isinstance(response, AgentResponse)
            assert response.content == "I'm doing great, thanks for asking!"

    @pytest.mark.asyncio
    async def test_process_combines_history_and_message(self, orchestrator, sample_request):
        """Test that orchestrator combines chat history and user message."""
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.tool_calls = None

        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_llm:
            await orchestrator.process(sample_request)

            # Verify LLM was called with combined messages
            call_args = mock_llm.call_args
            messages = call_args.kwargs.get('messages') or call_args.args[0]

            assert len(messages) == 3  # 2 history + 1 current
            assert messages[0].content == "Hello"
            assert messages[1].content == "Hi there!"
            assert messages[2].content == "How are you?"

    @pytest.mark.asyncio
    async def test_process_includes_system_message(self, orchestrator, sample_request):
        """Test that orchestrator includes system message."""
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.tool_calls = None

        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_llm:
            await orchestrator.process(sample_request)

            # Verify system message was passed
            call_args = mock_llm.call_args
            system_message = call_args.kwargs.get('system_message')

            assert system_message == "You are a helpful assistant."


@pytest.mark.unit
class TestAgentOrchestratorErrorHandling:
    """Tests for AgentOrchestrator error handling."""

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, orchestrator, sample_request):
        """Test handling of LLM authentication error."""
        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            side_effect=LLMAuthenticationError("Invalid API key")
        ):
            response = await orchestrator.process(sample_request)

            # Should return user-friendly error message
            assert isinstance(response, AgentResponse)
            assert "Configuration error" in response.content
            assert "Invalid OpenAI API key" in response.content

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, orchestrator, sample_request):
        """Test handling of LLM rate limit error."""
        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            side_effect=LLMRateLimitError("Rate limit exceeded")
        ):
            response = await orchestrator.process(sample_request)

            # Should return user-friendly error message
            assert isinstance(response, AgentResponse)
            assert "Too many requests" in response.content
            assert "wait" in response.content.lower()

    @pytest.mark.asyncio
    async def test_context_length_error_handling(self, orchestrator, sample_request):
        """Test handling of context length error."""
        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            side_effect=LLMContextLengthError("Context too long")
        ):
            response = await orchestrator.process(sample_request)

            # Should return user-friendly error message
            assert isinstance(response, AgentResponse)
            # LLMContextLengthError is subclass of LLMError, handled by LLMError catch
            assert "error" in response.content.lower()

    @pytest.mark.asyncio
    async def test_generic_llm_error_handling(self, orchestrator, sample_request):
        """Test handling of generic LLM error."""
        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            side_effect=LLMError("Some LLM error")
        ):
            response = await orchestrator.process(sample_request)

            # Should return user-friendly error message
            assert isinstance(response, AgentResponse)
            assert "Sorry" in response.content
            assert "error" in response.content.lower()

    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, orchestrator, sample_request):
        """Test handling of unexpected error."""
        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            side_effect=ValueError("Unexpected error")
        ):
            response = await orchestrator.process(sample_request)

            # Should return generic error message
            assert isinstance(response, AgentResponse)
            assert "unexpected error" in response.content.lower()
            assert "try again" in response.content.lower()


@pytest.mark.unit
class TestAgentOrchestratorIntegration:
    """Integration tests for AgentOrchestrator."""

    @pytest.mark.asyncio
    async def test_empty_chat_history(self, orchestrator):
        """Test processing with empty chat history."""
        from unittest.mock import MagicMock
        from uuid import UUID
        request = AgentRequest(
            chat_history=[],
            user_message=AgentMessage(role="user", content="Hello"),
            chat_id=UUID("00000000-0000-0000-0000-000000000001")
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hi!"
        mock_response.choices[0].message.tool_calls = None

        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            response = await orchestrator.process(request)

            assert isinstance(response, AgentResponse)
            assert response.content == "Hi!"

    @pytest.mark.asyncio
    async def test_long_chat_history(self, orchestrator):
        """Test processing with long chat history."""
        from unittest.mock import MagicMock
        from uuid import UUID
        # Create long history
        history = [
            AgentMessage(role="user" if i % 2 == 0 else "assistant", content=f"Message {i}")
            for i in range(20)
        ]

        request = AgentRequest(
            chat_history=history,
            user_message=AgentMessage(role="user", content="Latest message"),
            chat_id=UUID("00000000-0000-0000-0000-000000000001")
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.tool_calls = None

        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_llm:
            response = await orchestrator.process(request)

            # Verify all messages were passed
            call_args = mock_llm.call_args
            messages = call_args.kwargs.get('messages') or call_args.args[0]
            assert len(messages) == 21  # 20 history + 1 current

            assert isinstance(response, AgentResponse)
            assert response.content == "Response"

    @pytest.mark.asyncio
    async def test_error_recovery_does_not_raise(self, orchestrator, sample_request):
        """Test that errors are caught and don't propagate."""
        # Even with exception, should not raise
        with patch.object(
            orchestrator.llm_client,
            'chat_completion',
            new_callable=AsyncMock,
            side_effect=Exception("Critical error")
        ):
            # Should not raise, should return error response
            response = await orchestrator.process(sample_request)
            assert isinstance(response, AgentResponse)
            assert len(response.content) > 0