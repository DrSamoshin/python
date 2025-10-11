"""
    User repository for database operations.
    Encapsulates all database queries related to users.
    Repository layer does NOT commit - only executes SQL.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, email: str) -> User:
        """Create new user. Does NOT commit."""
        user = User(name=name, email=email)
        self.session.add(user)
        return user

    async def update_name(self, user: User, name: str) -> User:
        """Update user name. Does NOT commit."""
        user.name = name
        return user

    async def delete(self, user: User) -> None:
        """Delete user. Does NOT commit."""
        await self.session.delete(user)
