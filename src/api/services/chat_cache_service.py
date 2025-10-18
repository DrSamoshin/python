from __future__ import annotations
import json
from uuid import UUID
from redis.asyncio import Redis
from src.api.core.configs import settings
from src.models import Message, MessageRole
from typing import Sequence
import logging
from src.api.v1.schemas import MessageSchema

logger = logging.getLogger(__name__)


class ChatCacheService:
    """Service for caching chat messages in Redis."""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.max_messages = settings.redis_max_messages
        self.ttl = settings.redis_cache_ttl

    def _get_messages_key(self, chat_id: UUID) -> str:
        """Get Redis key for chat messages list."""
        return f"chat:{chat_id}:messages"

    def _message_to_dict(self, message: Message) -> dict:
        """Convert Message model to dict for Redis."""
        schema = MessageSchema.model_validate(message)
        return schema.model_dump(mode='json')

    def _dict_to_message_data(self, data: dict) -> MessageSchema:
        """Convert Redis dict back to MessageSchema."""
        return MessageSchema.model_validate(data)

    async def get_messages(self, chat_id: UUID) -> list[MessageSchema] | None:
        """
        Get cached messages for a chat.
        Returns list of MessageSchema or None if cache is empty.
        """
        key = self._get_messages_key(chat_id)
        messages_json = await self.redis.lrange(key, 0, -1)

        if not messages_json:
            logger.debug(f"Cache miss for chat {chat_id}")
            return None

        logger.debug(f"Cache hit for chat {chat_id}, {len(messages_json)} messages")
        return [
            self._dict_to_message_data(json.loads(msg))
            for msg in messages_json
        ]

    async def set_messages(self, chat_id: UUID, messages: Sequence[Message]) -> None:
        """
        Cache messages for a chat.
        Stores last N messages based on settings.redis_max_messages.
        """
        key = self._get_messages_key(chat_id)

        # Clear existing cache
        await self.redis.delete(key)

        # Take only last N messages
        messages_to_cache = messages[-self.max_messages:]

        if messages_to_cache:
            # Convert to JSON and push to list
            messages_json = [
                json.dumps(self._message_to_dict(msg))
                for msg in messages_to_cache
            ]
            await self.redis.rpush(key, *messages_json)

            # Set expiration
            await self.redis.expire(key, self.ttl)
            logger.debug(f"Cached {len(messages_to_cache)} messages for chat {chat_id}")

    async def add_message(self, message: Message) -> None:
        """
        Add a single message to cache.
        Maintains max_messages limit by removing oldest if needed.
        """
        key = self._get_messages_key(message.chat_id)
        message_json = json.dumps(self._message_to_dict(message))

        # Add to end of list
        await self.redis.rpush(key, message_json)

        # Trim to keep only last N messages
        await self.redis.ltrim(key, -self.max_messages, -1)

        # Refresh expiration
        await self.redis.expire(key, self.ttl)
        logger.debug(f"Added message {message.id} to cache for chat {message.chat_id}")

    async def clear_chat(self, chat_id: UUID) -> None:
        """Clear cached messages for a chat."""
        key = self._get_messages_key(chat_id)
        await self.redis.delete(key)
        logger.debug(f"Cleared cache for chat {chat_id}")

