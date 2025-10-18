from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.chat_repository import ChatRepository
from src.models import Chat
from src.api.exceptions import NotFoundException, ForbiddenException
from typing import Sequence


class ChatService:
    """Service for chat business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.chat_repo = ChatRepository(session)

    async def create_chat(
            self,
            user_id: UUID,
            title: str | None = None
    ) -> Chat:
        """Create a new chat for user."""
        chat = await self.chat_repo.create(user_id=user_id, title=title)
        await self.session.commit()
        return chat

    async def get_chat(self, chat_id: UUID, user_id: UUID) -> Chat:
        """
        Get chat by ID.
        Raises NotFoundException if chat doesn't exist.
        Raises ForbiddenException if chat doesn't belong to user.
        """
        chat = await self.chat_repo.get_by_id(chat_id)

        if not chat:
            raise NotFoundException(f"Chat {chat_id} not found")

        if chat.user_id != user_id:
            raise ForbiddenException("Access denied to this chat")

        return chat

    async def get_user_chats(
            self,
            user_id: UUID,
            limit: int = 50,
            offset: int = 0
    ) -> Sequence[Chat]:
        """Get all chats for a user."""
        return await self.chat_repo.get_user_chats(
            user_id=user_id,
            limit=limit,
            offset=offset
        )

    async def update_chat_title(
            self,
            chat_id: UUID,
            user_id: UUID,
            title: str
    ) -> Chat:
        """
        Update chat title.
        Raises NotFoundException if chat doesn't exist.
        Raises ForbiddenException if chat doesn't belong to user.
        """
        # Check ownership
        await self.get_chat(chat_id, user_id)

        chat = await self.chat_repo.update_title(chat_id, title)
        await self.session.commit()
        return chat

    async def delete_chat(self, chat_id: UUID, user_id: UUID) -> bool:
        """
        Delete chat.
        Raises NotFoundException if chat doesn't exist.
        Raises ForbiddenException if chat doesn't belong to user.
        """
        # Check ownership
        await self.get_chat(chat_id, user_id)

        result = await self.chat_repo.delete(chat_id)
        await self.session.commit()
        return result
