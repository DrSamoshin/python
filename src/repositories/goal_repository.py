"""Goal repository for database operations."""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Goal, GoalStatus


class GoalRepository:
    """Repository for Goal CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self,
            chat_id: UUID,
            title: str,
            description: str | None = None,
            parent_id: UUID | None = None
    ) -> Goal:
        """Create a new goal with IN_PROGRESS status."""
        goal = Goal(
            chat_id=chat_id,
            title=title,
            description=description,
            status=GoalStatus.IN_PROGRESS,
            parent_id=parent_id
        )
        self.session.add(goal)
        await self.session.flush()
        await self.session.refresh(goal)
        return goal

    async def get_by_id(self, goal_id: UUID) -> Goal | None:
        """Get goal by ID."""
        result = await self.session.execute(
            select(Goal).where(Goal.id == goal_id)
        )
        return result.scalar_one_or_none()

    async def get_by_chat(
            self,
            chat_id: UUID,
            status: GoalStatus | None = None,
            parent_id: UUID | None = None
    ) -> list[Goal]:
        """
        Get goals by chat_id with optional filtering.

        Args:
            chat_id: Chat UUID
            status: Optional status filter
            parent_id: Optional parent_id filter (None = root goals only)
        """
        query = select(Goal).where(Goal.chat_id == chat_id)

        if status is not None:
            query = query.where(Goal.status == status)

        if parent_id is not None:
            query = query.where(Goal.parent_id == parent_id)
        else:
            # If parent_id not specified, return only root goals
            query = query.where(Goal.parent_id.is_(None))

        query = query.order_by(Goal.created_at)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_by_chat(self, chat_id: UUID) -> list[Goal]:
        """Get all goals for a chat (including sub-goals)."""
        result = await self.session.execute(
            select(Goal)
            .where(Goal.chat_id == chat_id)
            .order_by(Goal.created_at)
        )
        return list(result.scalars().all())

    async def update_status(self, goal_id: UUID, status: GoalStatus) -> Goal | None:
        """Update goal status."""
        goal = await self.get_by_id(goal_id)
        if goal:
            goal.status = status
            await self.session.flush()
            await self.session.refresh(goal)
        return goal

    async def update(
            self,
            goal_id: UUID,
            title: str | None = None,
            description: str | None = None
    ) -> Goal | None:
        """Update goal title and description."""
        goal = await self.get_by_id(goal_id)
        if goal:
            if title is not None:
                goal.title = title
            if description is not None:
                goal.description = description

            await self.session.flush()
            await self.session.refresh(goal)
        return goal

    async def link_to_parent(self, goal_id: UUID, parent_id: UUID | None) -> Goal | None:
        """
        Link goal to a parent goal or make it independent.

        Args:
            goal_id: Goal to update
            parent_id: Parent goal ID (None = make independent)

        Returns:
            Updated goal or None if not found
        """
        goal = await self.get_by_id(goal_id)
        if goal:
            goal.parent_id = parent_id
            await self.session.flush()
            await self.session.refresh(goal)
        return goal

    async def delete(self, goal_id: UUID) -> bool:
        """Delete goal by ID (cascade deletes sub-goals)."""
        goal = await self.get_by_id(goal_id)
        if goal:
            await self.session.delete(goal)
            await self.session.flush()
            return True
        return False