"""Chat session service - handles chat message processing logic."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.api.services.message_service import MessageService
from src.models import MessageRole
from src.api.core.configs import settings
from src.agent import AgentOrchestrator, AgentMessage, AgentRequest


class ChatMessageResult:
    """Result of processing user message."""

    def __init__(self, user_message, assistant_message):
        self.user_message = user_message
        self.assistant_message = assistant_message


class ChatSessionService:
    """Service for managing chat sessions and message processing."""

    def __init__(self, session: AsyncSession, redis: Redis):
        self.session = session
        self.redis = redis
        self.message_service = MessageService(session, redis)
        self.agent_orchestrator = AgentOrchestrator()

        # Cache for chat histories (chat_id -> list of messages)
        self.chat_history_cache = {}

    async def process_user_message(
            self,
            chat_id: UUID,
            content: str
    ) -> ChatMessageResult:
        """
        Process user message and generate assistant response.

        Args:
            chat_id: Chat UUID
            content: User message content

        Returns:
            ChatMessageResult with user and assistant messages
        """
        # 1. Save user message
        user_message = await self.message_service.create_message(
            chat_id=chat_id,
            role=MessageRole.USER,
            content=content
        )

        # 2. Get or load chat history
        history = await self._get_or_load_history(chat_id)

        # 3. Generate assistant response using AgentOrchestrator
        assistant_content = await self._generate_response(history, user_message)

        # 4. Save assistant message
        assistant_message = await self.message_service.create_message(
            chat_id=chat_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content
        )

        # 5. Update history cache
        await self._update_history_cache(chat_id, user_message, assistant_message)

        return ChatMessageResult(
            user_message=user_message,
            assistant_message=assistant_message
        )

    async def load_initial_history(self, chat_id: UUID) -> list:
        """Load initial chat history for a session."""
        history = await self.message_service.get_chat_history(
            chat_id,
            limit=settings.chat_history_limit
        )
        self.chat_history_cache[chat_id] = history
        return history

    async def _get_or_load_history(self, chat_id: UUID) -> list:
        """Get history from cache or load from DB."""
        if chat_id not in self.chat_history_cache:
            self.chat_history_cache[chat_id] = await self.message_service.get_chat_history(
                chat_id,
                limit=settings.chat_history_limit
            )
        return self.chat_history_cache[chat_id]

    async def _update_history_cache(self, chat_id: UUID, user_message, assistant_message):
        """Update history cache with new messages."""
        if chat_id in self.chat_history_cache:
            self.chat_history_cache[chat_id].append(user_message)
            self.chat_history_cache[chat_id].append(assistant_message)

            # Keep only configured number of messages
            limit = settings.chat_history_limit
            if len(self.chat_history_cache[chat_id]) > limit:
                self.chat_history_cache[chat_id] = self.chat_history_cache[chat_id][-limit:]

    async def _generate_response(self, chat_history: list, user_message) -> str:
        """
        Generate assistant response using AgentOrchestrator.

        Args:
            chat_history: List of SQLAlchemy Message objects
            user_message: Current user's SQLAlchemy Message object

        Returns:
            Generated response content
        """
        # Convert SQLAlchemy Message objects to AgentMessage DTOs
        agent_history = [
            AgentMessage(
                role=msg.role.value,  # MessageRole enum to string
                content=msg.content
            )
            for msg in chat_history
        ]

        # Create current user message DTO
        agent_user_message = AgentMessage(
            role=user_message.role.value,
            content=user_message.content
        )

        # Create AgentRequest
        agent_request = AgentRequest(
            chat_history=agent_history,
            user_message=agent_user_message
        )

        # Process through AgentOrchestrator
        agent_response = await self.agent_orchestrator.process(agent_request)

        return agent_response.content
