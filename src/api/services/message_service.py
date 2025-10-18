from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.repositories.message_repository import MessageRepository
from src.repositories.chat_repository import ChatRepository
from src.api.services.chat_cache_service import ChatCacheService
from src.models import Message, MessageRole
from src.api.v1.schemas import MessageSchema
from src.api.exceptions import NotFoundException
from typing import Sequence

import logging

logger = logging.getLogger(__name__)


class MessageService:
    """Service for message business logic with Redis caching."""

    def __init__(self, session: AsyncSession, redis: Redis):
        self.session = session
        self.message_repo = MessageRepository(session)
        self.chat_repo = ChatRepository(session)
        self.cache_service = ChatCacheService(redis)

    async def create_message(
            self,
            chat_id: UUID,
            role: MessageRole,
            content: str
    ) -> Message:
        """
        Create a new message and add to cache.
        """
        # Verify chat exists
        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat:
            raise NotFoundException(f"Chat {chat_id} not found")

        # Create message in DB
        message = await self.message_repo.create(
            chat_id=chat_id,
            role=role,
            content=content
        )
        await self.session.commit()
        await self.session.refresh(message)

        # Add to cache
        try:
            await self.cache_service.add_message(message)
        except Exception as e:
            logger.error(f"Failed to cache message {message.id}: {e}")

        return message

    async def get_chat_history(
            self,
            chat_id: UUID,
            use_cache: bool = True
    ) -> list[MessageSchema]:
        """
        Get chat message history.
        First tries Redis cache, falls back to PostgreSQL.
        Returns messages in chronological order (oldest first).
        """
        # Try cache first
        if use_cache:
            cached_messages = await self.cache_service.get_messages(chat_id)
            if cached_messages is not None:
                logger.debug(f"Returning {len(cached_messages)} messages from cache")
                return cached_messages

        # Cache miss - load from DB
        logger.debug(f"Cache miss, loading from DB for chat {chat_id}")
        messages = await self.message_repo.get_recent_messages(
            chat_id=chat_id,
            limit=self.cache_service.max_messages
        )

        # Populate cache for next time
        if messages:
            try:
                await self.cache_service.set_messages(chat_id, messages)
            except Exception as e:
                logger.error(f"Failed to populate cache for chat {chat_id}: {e}")

        # Convert to schemas
        return [MessageSchema.model_validate(msg) for msg in messages]

    async def get_all_messages(
            self,
            chat_id: UUID,
            limit: int | None = None,
            offset: int = 0
    ) -> Sequence[Message]:
        """
        Get all messages for a chat from PostgreSQL.
        Used for admin/analytics, not regular chat.
        """
        return await self.message_repo.get_chat_messages(
            chat_id=chat_id,
            limit=limit,
            offset=offset
        )

    async def clear_chat_cache(self, chat_id: UUID) -> None:
        """Clear Redis cache for a chat."""
        await self.cache_service.clear_chat(chat_id)
        logger.info(f"Cleared cache for chat {chat_id}")
