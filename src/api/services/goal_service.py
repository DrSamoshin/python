"""Goal service for business logic."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import GoalStatus
from src.repositories.goal_repository import GoalRepository


class GoalService:
    """Service for Goal business logic."""

    def __init__(self, session: AsyncSession):
        self.repo = GoalRepository(session)

    async def create_goal(
            self,
            chat_id: UUID,
            title: str,
            description: str | None = None,
            parent_id: UUID | None = None
    ):
        """Create a new goal."""
        return await self.repo.create(
            chat_id=chat_id,
            title=title,
            description=description,
            parent_id=parent_id
        )

    async def list_goals(
            self,
            chat_id: UUID,
            status: GoalStatus | None = None,
            parent_id: UUID | None = None
    ):
        """Get goals by chat_id with optional filtering."""
        return await self.repo.get_by_chat(
            chat_id=chat_id,
            status=status,
            parent_id=parent_id
        )

    async def get_all_goals(self, chat_id: UUID):
        """Get all goals for a chat (including sub-goals)."""
        return await self.repo.get_all_by_chat(chat_id)

    async def update_goal_status(self, goal_id: UUID, status: GoalStatus):
        """Update goal status."""
        return await self.repo.update_status(goal_id, status)

    async def update_goal(
            self,
            goal_id: UUID,
            title: str | None = None,
            description: str | None = None
    ):
        """Update goal title and/or description."""
        return await self.repo.update(
            goal_id=goal_id,
            title=title,
            description=description
        )

    async def delete_goal(self, goal_id: UUID) -> bool:
        """Delete goal by ID (cascade deletes sub-goals)."""
        return await self.repo.delete(goal_id)

    async def link_goal_to_parent(
            self,
            goal_id: UUID,
            parent_id: UUID | None
    ):
        """Link goal to a parent or make it independent."""
        return await self.repo.link_to_parent(goal_id, parent_id)