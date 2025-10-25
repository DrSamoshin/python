"""Unit tests for ChatSessionService."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api.services.chat_session_service import ChatMessageResult
from src.models import MessageRole
from src.agent.dto import AgentResponse


@pytest.mark.unit
class TestChatSessionServiceProcessing:
    """Tests for message processing flow."""

    async def test_process_user_message_success(
            self,
            chat_service,
            sample_chat_id,
            sample_user_id,
            mock_user_message,
            mock_assistant_message
    ):
        """Test successful message processing."""
        # Mock message service
        chat_service.message_service.create_message = AsyncMock(
            side_effect=[mock_user_message, mock_assistant_message]
        )
        chat_service.message_service.get_chat_history = AsyncMock(return_value=[])

        # Mock agent orchestrator
        chat_service.agent_orchestrator.process = AsyncMock(
            return_value=AgentResponse(content="Hi there!")
        )

        # Process message
        result = await chat_service.process_user_message(
            chat_id=sample_chat_id,
            content="Hello",
            user_id=sample_user_id
        )

        # Verify result
        assert isinstance(result, ChatMessageResult)
        assert result.user_message == mock_user_message
        assert result.assistant_message == mock_assistant_message

        # Verify message service was called correctly
        assert chat_service.message_service.create_message.call_count == 2
        first_call = chat_service.message_service.create_message.call_args_list[0]
        assert first_call.kwargs['chat_id'] == sample_chat_id
        assert first_call.kwargs['role'] == MessageRole.USER
        assert first_call.kwargs['content'] == "Hello"

    async def test_process_loads_history_once(self, chat_service, sample_chat_id, sample_user_id):
        """Test that history is loaded from cache after first load."""
        mock_user_msg = AsyncMock()
        mock_user_msg.role = MessageRole.USER
        mock_user_msg.content = "Message"
        mock_user_msg.tool_call_data = None
        mock_user_msg.chat_id = sample_chat_id

        mock_assistant_msg = AsyncMock()
        mock_assistant_msg.role = MessageRole.ASSISTANT
        mock_assistant_msg.content = "Response"
        mock_assistant_msg.tool_call_data = None

        chat_service.message_service.create_message = AsyncMock(
            side_effect=[mock_user_msg, mock_assistant_msg, mock_user_msg, mock_assistant_msg]
        )
        chat_service.message_service.get_chat_history = AsyncMock(return_value=[])
        chat_service.agent_orchestrator.process = AsyncMock(
            return_value=AgentResponse(content="Response")
        )

        # First message - should load history
        await chat_service.process_user_message(sample_chat_id, "Message", sample_user_id)

        # Verify history was loaded
        assert chat_service.message_service.get_chat_history.call_count == 1

        # Second message - should use cache
        await chat_service.process_user_message(sample_chat_id, "Message 2", sample_user_id)

        # Should still be 1 (cached)
        assert chat_service.message_service.get_chat_history.call_count == 1

    async def test_process_updates_history_cache(
            self,
            chat_service,
            sample_chat_id,
            sample_user_id,
            mock_user_message,
            mock_assistant_message
    ):
        """Test that history cache is updated with new messages."""
        chat_service.message_service.create_message = AsyncMock(
            side_effect=[mock_user_message, mock_assistant_message]
        )
        chat_service.message_service.get_chat_history = AsyncMock(return_value=[])
        chat_service.agent_orchestrator.process = AsyncMock(
            return_value=AgentResponse(content="Hi")
        )

        # Process message
        await chat_service.process_user_message(sample_chat_id, "Hello", sample_user_id)

        # Verify cache was updated
        assert sample_chat_id in chat_service.chat_history_cache
        assert len(chat_service.chat_history_cache[sample_chat_id]) == 2
        assert chat_service.chat_history_cache[sample_chat_id][0] == mock_user_message
        assert chat_service.chat_history_cache[sample_chat_id][1] == mock_assistant_message


@pytest.mark.unit
class TestChatSessionServiceHistoryManagement:
    """Tests for history loading and caching."""

    async def test_load_initial_history(self, chat_service, sample_chat_id, mock_user_message, mock_assistant_message):
        """Test loading initial chat history."""
        mock_history = [mock_user_message, mock_assistant_message]

        chat_service.message_service.get_chat_history = AsyncMock(
            return_value=mock_history
        )

        # Load history
        result = await chat_service.load_initial_history(sample_chat_id)

        # Verify
        assert result == mock_history
        assert sample_chat_id in chat_service.chat_history_cache
        assert chat_service.chat_history_cache[sample_chat_id] == mock_history

    async def test_load_initial_history_with_limit(self, chat_service, sample_chat_id):
        """Test that history is loaded with configured limit."""
        chat_service.message_service.get_chat_history = AsyncMock(return_value=[])

        with patch('src.api.services.chat_session_service.settings') as mock_settings:
            mock_settings.chat_history_limit = 15

            await chat_service.load_initial_history(sample_chat_id)

            # Verify limit was passed
            call_args = chat_service.message_service.get_chat_history.call_args
            assert call_args.kwargs.get('limit') == 15

    async def test_history_cache_limits_size(self, chat_service, sample_chat_id):
        """Test that history cache respects size limit."""
        with patch('src.api.services.chat_session_service.settings') as mock_settings:
            mock_settings.chat_history_limit = 3

            # Pre-populate cache with 2 messages
            msg1 = AsyncMock()
            msg1.role = MessageRole.USER
            msg1.content = "Msg 1"

            msg2 = AsyncMock()
            msg2.role = MessageRole.ASSISTANT
            msg2.content = "Response 1"

            chat_service.chat_history_cache[sample_chat_id] = [msg1, msg2]

            # Add new pair of messages (should exceed limit)
            user_msg = AsyncMock()
            user_msg.role = MessageRole.USER
            user_msg.content = "Msg 2"

            assistant_msg = AsyncMock()
            assistant_msg.role = MessageRole.ASSISTANT
            assistant_msg.content = "Response 2"

            await chat_service._update_history_cache(
                sample_chat_id,
                user_msg,
                assistant_msg
            )

            # Should keep only last 3 messages (trimmed first one)
            assert len(chat_service.chat_history_cache[sample_chat_id]) == 3
            assert chat_service.chat_history_cache[sample_chat_id][-1] == assistant_msg


@pytest.mark.unit
class TestChatSessionServiceAgentIntegration:
    """Tests for Agent system integration."""

    async def test_generate_response_converts_messages(self, chat_service, sample_chat_id, sample_user_id, mock_user_message):
        """Test that SQLAlchemy messages are converted to AgentMessage DTOs."""
        # Mock SQLAlchemy messages
        history_msg1 = AsyncMock()
        history_msg1.role = MessageRole.USER
        history_msg1.content = "Hello"
        history_msg1.tool_call_data = None

        history_msg2 = AsyncMock()
        history_msg2.role = MessageRole.ASSISTANT
        history_msg2.content = "Hi"
        history_msg2.tool_call_data = None

        history = [history_msg1, history_msg2]

        user_message = AsyncMock()
        user_message.role = MessageRole.USER
        user_message.content = "How are you?"
        user_message.chat_id = sample_chat_id

        chat_service.agent_orchestrator.process = AsyncMock(
            return_value=AgentResponse(content="I'm great!")
        )

        # Generate response
        result = await chat_service._generate_response(history, user_message, sample_user_id, sample_chat_id)

        # Verify AgentOrchestrator was called
        assert chat_service.agent_orchestrator.process.called

        # Verify AgentRequest structure
        call_args = chat_service.agent_orchestrator.process.call_args
        agent_request = call_args.args[0]

        # Check history conversion
        assert len(agent_request.chat_history) == 2
        assert agent_request.chat_history[0].role == "user"
        assert agent_request.chat_history[0].content == "Hello"
        assert agent_request.chat_history[1].role == "assistant"
        assert agent_request.chat_history[1].content == "Hi"

        # Check user message conversion
        assert agent_request.user_message.role == "user"
        assert agent_request.user_message.content == "How are you?"

        # Check chat_id was passed
        assert agent_request.chat_id == sample_chat_id

        # Check result
        assert result.content == "I'm great!"

    async def test_generate_response_with_empty_history(self, chat_service, sample_chat_id, sample_user_id):
        """Test response generation with empty chat history."""
        user_message = AsyncMock()
        user_message.role = MessageRole.USER
        user_message.content = "Hello"
        user_message.chat_id = sample_chat_id

        chat_service.agent_orchestrator.process = AsyncMock(
            return_value=AgentResponse(content="Hi!")
        )

        result = await chat_service._generate_response([], user_message, sample_user_id, sample_chat_id)

        # Verify empty history was passed
        call_args = chat_service.agent_orchestrator.process.call_args
        agent_request = call_args.args[0]

        assert len(agent_request.chat_history) == 0
        assert agent_request.user_message.content == "Hello"
        assert result.content == "Hi!"

    async def test_generate_response_preserves_agent_errors(self, chat_service, sample_chat_id, sample_user_id):
        """Test that agent errors are returned as content (not raised)."""
        user_message = AsyncMock()
        user_message.role = MessageRole.USER
        user_message.content = "Hello"
        user_message.chat_id = sample_chat_id

        # Agent returns error message in response
        chat_service.agent_orchestrator.process = AsyncMock(
            return_value=AgentResponse(
                content="Configuration error: Invalid OpenAI API key. Please contact support."
            )
        )

        result = await chat_service._generate_response([], user_message, sample_user_id, sample_chat_id)

        # Error message should be returned as content
        assert "Configuration error" in result.content
        assert "Invalid OpenAI API key" in result.content


@pytest.mark.unit
class TestChatSessionServiceIntegration:
    """Integration tests for ChatSessionService."""

    async def test_full_conversation_flow(self, chat_service, sample_chat_id, sample_user_id):
        """Test complete conversation flow with multiple messages."""
        messages = []

        def create_message_side_effect(chat_id, role, content, tool_call_data=None):
            msg = AsyncMock()
            msg.chat_id = chat_id
            msg.role = role
            msg.content = content
            msg.tool_call_data = tool_call_data
            messages.append(msg)
            return msg

        chat_service.message_service.create_message = AsyncMock(
            side_effect=create_message_side_effect
        )
        chat_service.message_service.get_chat_history = AsyncMock(return_value=[])

        # Mock agent responses
        responses = ["Hi there!", "I'm doing great!", "Goodbye!"]
        chat_service.agent_orchestrator.process = AsyncMock(
            side_effect=[AgentResponse(content=r) for r in responses]
        )

        # Simulate 3 message exchanges
        for i, user_content in enumerate(["Hello", "How are you?", "Bye"]):
            result = await chat_service.process_user_message(sample_chat_id, user_content, sample_user_id)

            assert result.user_message.content == user_content
            assert result.assistant_message.content == responses[i]

        # Verify all messages were created
        assert len(messages) == 6  # 3 user + 3 assistant

        # Verify cache has all messages
        assert len(chat_service.chat_history_cache[sample_chat_id]) == 6

    async def test_multiple_chats_separate_caches(self, chat_service):
        """Test that different chats have separate history caches."""
        chat_id_1 = uuid4()
        chat_id_2 = uuid4()

        # Create separate mocks for each message
        mock_user_msg_1 = AsyncMock()
        mock_user_msg_1.role = MessageRole.USER
        mock_user_msg_1.content = "Hello 1"
        mock_user_msg_1.chat_id = chat_id_1
        mock_user_msg_1.tool_call_data = None

        mock_assistant_msg_1 = AsyncMock()
        mock_assistant_msg_1.role = MessageRole.ASSISTANT
        mock_assistant_msg_1.content = "Hi 1"
        mock_assistant_msg_1.tool_call_data = None

        mock_user_msg_2 = AsyncMock()
        mock_user_msg_2.role = MessageRole.USER
        mock_user_msg_2.content = "Hello 2"
        mock_user_msg_2.chat_id = chat_id_2
        mock_user_msg_2.tool_call_data = None

        mock_assistant_msg_2 = AsyncMock()
        mock_assistant_msg_2.role = MessageRole.ASSISTANT
        mock_assistant_msg_2.content = "Hi 2"
        mock_assistant_msg_2.tool_call_data = None

        chat_service.message_service.create_message = AsyncMock(
            side_effect=[mock_user_msg_1, mock_assistant_msg_1, mock_user_msg_2, mock_assistant_msg_2]
        )
        # Return new empty list each time to avoid shared state
        chat_service.message_service.get_chat_history = AsyncMock(side_effect=lambda *args, **kwargs: [])
        chat_service.agent_orchestrator.process = AsyncMock(
            return_value=AgentResponse(content="Hi")
        )

        # Process message in chat 1
        await chat_service.process_user_message(chat_id_1, "Hello", uuid4())

        # Process message in chat 2
        await chat_service.process_user_message(chat_id_2, "Hello", uuid4())

        # Verify separate caches
        assert chat_id_1 in chat_service.chat_history_cache
        assert chat_id_2 in chat_service.chat_history_cache
        assert len(chat_service.chat_history_cache[chat_id_1]) == 2
        assert len(chat_service.chat_history_cache[chat_id_2]) == 2

        # Verify correct messages in each cache
        assert chat_service.chat_history_cache[chat_id_1][0] == mock_user_msg_1
        assert chat_service.chat_history_cache[chat_id_1][1] == mock_assistant_msg_1
        assert chat_service.chat_history_cache[chat_id_2][0] == mock_user_msg_2
        assert chat_service.chat_history_cache[chat_id_2][1] == mock_assistant_msg_2