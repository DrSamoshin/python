from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Message, MessageRole
from typing import Sequence


class MessageRepository:
    """Repository for Message database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self,
            chat_id: UUID,
            role: MessageRole,
            content: str | None = None,
            tool_call_data: dict | None = None
    ) -> Message:
        """Create a new message."""
        message = Message(
            chat_id=chat_id,
            role=role,
            content=content,
            tool_call_data=tool_call_data
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get_chat_messages(
            self,
            chat_id: UUID,
            limit: int | None = None,
            offset: int = 0
    ) -> Sequence[Message]:
        """
        Get messages for a chat, ordered by created_at asc.
        If limit is None, returns all messages.
        """
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
        )

        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recent_messages(
            self,
            chat_id: UUID,
            limit: int = 50
    ) -> Sequence[Message]:
        """
        Get N most recent messages for a chat, ordered by created_at asc.
        This is useful for loading chat history from newest to oldest,
        then reversing for display.
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        # Return in chronological order
        return list(reversed(messages))

    async def delete_chat_messages(self, chat_id: UUID) -> int:
        """Delete all messages in a chat. Returns count of deleted messages."""
        messages = await self.get_chat_messages(chat_id)
        count = len(messages)
        for message in messages:
            await self.session.delete(message)
        await self.session.flush()
        return count
