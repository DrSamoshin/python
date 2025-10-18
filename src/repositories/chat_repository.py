from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Chat
from typing import Sequence


class ChatRepository:
    """Repository for Chat database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, title: str | None = None) -> Chat:
        """Create a new chat."""
        chat = Chat(user_id=user_id, title=title)
        self.session.add(chat)
        await self.session.flush()
        await self.session.refresh(chat)
        return chat

    async def get_by_id(self, chat_id: UUID) -> Chat | None:
        """Get chat by ID."""
        result = await self.session.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        return result.scalar_one_or_none()

    async def get_user_chats(
            self,
            user_id: UUID,
            limit: int = 50,
            offset: int = 0
    ) -> Sequence[Chat]:
        """Get all chats for a user, ordered by updated_at desc."""
        result = await self.session.execute(
            select(Chat)
            .where(Chat.user_id == user_id)
            .order_by(Chat.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def update_title(self, chat_id: UUID, title: str) -> Chat | None:
        """Update chat title."""
        chat = await self.get_by_id(chat_id)
        if chat:
            chat.title = title
            await self.session.flush()
            await self.session.refresh(chat)
        return chat

    async def delete(self, chat_id: UUID) -> bool:
        """Delete chat by ID."""
        chat = await self.get_by_id(chat_id)
        if chat:
            await self.session.delete(chat)
            await self.session.flush()
            return True
        return False
