"""
    User service layer.
    Contains business logic and transaction management.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.user_repository import UserRepository
from src.models.user import User
from src.api.exceptions import UserAlreadyExistsError, UserNotFoundError


class UserService:
    """Service for user business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def create_user(self, name: str, email: str) -> User:
        """
        Create new user.
        Raises UserAlreadyExistsError if email already exists.
        """
        # Check if email already exists
        existing_user = await self.repo.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError(f"User with email {email} already exists")

        # Create user
        user = await self.repo.create(name=name, email=email)

        # Commit transaction
        try:
            await self.session.commit()
            await self.session.refresh(user)
        except IntegrityError:
            await self.session.rollback()
            raise UserAlreadyExistsError(f"User with email {email} already exists")

        return user

    async def get_user(self, user_id: UUID) -> User:
        """
        Get user by ID.
        Raises UserNotFoundError if not found.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email. Returns None if not found."""
        return await self.repo.get_by_email(email)

    async def update_user_name(self, user_id: UUID, name: str) -> User:
        """
        Update user name.
        Raises UserNotFoundError if user not found.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        user = await self.repo.update_name(user, name)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: UUID) -> None:
        """
        Delete user.
        Raises UserNotFoundError if user not found.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        await self.repo.delete(user)
        await self.session.commit()
