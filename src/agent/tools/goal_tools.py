"""Tools for managing goals."""

from typing import Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.tools.base import BaseTool
from src.api.services.goal_service import GoalService
from src.models import GoalStatus


class CreateGoalTool(BaseTool):
    """Tool for creating a new goal."""

    @property
    def name(self) -> str:
        return "create_goal"

    @property
    def description(self) -> str:
        return "Create a new goal for the user. Goals help track objectives and tasks."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Goal title (max 500 characters)"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed goal description (optional)"
                },
                "parent_id": {
                    "type": "string",
                    "description": "Parent goal UUID to create a sub-goal (optional)"
                }
            },
            "required": ["title"]
        }

    async def execute(
            self,
            session: AsyncSession,
            context: dict[str, Any],
            **kwargs
    ) -> dict[str, Any]:
        """Execute goal creation."""
        chat_id = context.get("chat_id")
        if not chat_id:
            return {"error": "chat_id not found in context"}

        title = kwargs.get("title")
        description = kwargs.get("description")
        parent_id_str = kwargs.get("parent_id")

        parent_id = None
        if parent_id_str:
            try:
                parent_id = UUID(parent_id_str)
            except ValueError:
                return {"error": f"Invalid parent_id format: {parent_id_str}"}

        goal_service = GoalService(session)
        goal = await goal_service.create_goal(
            chat_id=chat_id,
            title=title,
            description=description,
            parent_id=parent_id
        )

        return {
            "success": True,
            "goal_id": str(goal.id),
            "title": goal.title,
            "status": goal.status.value,
            "created_at": goal.created_at.isoformat()
        }


class ListGoalsTool(BaseTool):
    """Tool for listing goals."""

    @property
    def name(self) -> str:
        return "list_goals"

    @property
    def description(self) -> str:
        return "List user's goals with optional filtering by status"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["in_progress", "completed", "cancelled", "blocked"],
                    "description": "Filter by goal status (optional)"
                },
                "include_subgoals": {
                    "type": "boolean",
                    "description": "Include all sub-goals in results (default: false, shows only root goals)"
                }
            },
            "required": []
        }

    async def execute(
            self,
            session: AsyncSession,
            context: dict[str, Any],
            **kwargs
    ) -> dict[str, Any]:
        """Execute goal listing."""
        chat_id = context.get("chat_id")
        if not chat_id:
            return {"error": "chat_id not found in context"}

        status_str = kwargs.get("status")
        include_subgoals = kwargs.get("include_subgoals", False)

        status = None
        if status_str:
            try:
                status = GoalStatus(status_str)
            except ValueError:
                return {"error": f"Invalid status: {status_str}"}

        goal_service = GoalService(session)

        if include_subgoals:
            goals = await goal_service.get_all_goals(chat_id)
        else:
            goals = await goal_service.list_goals(chat_id, status=status)

        return {
            "success": True,
            "count": len(goals),
            "goals": [
                {
                    "id": str(g.id),
                    "title": g.title,
                    "description": g.description,
                    "status": g.status.value,
                    "parent_id": str(g.parent_id) if g.parent_id else None,
                    "created_at": g.created_at.isoformat(),
                    "updated_at": g.updated_at.isoformat()
                }
                for g in goals
            ]
        }


class UpdateGoalStatusTool(BaseTool):
    """Tool for updating goal status."""

    @property
    def name(self) -> str:
        return "update_goal_status"

    @property
    def description(self) -> str:
        return "Update the status of a goal (in_progress, completed, cancelled, blocked)"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "goal_id": {
                    "type": "string",
                    "description": "Goal UUID to update"
                },
                "status": {
                    "type": "string",
                    "enum": ["in_progress", "completed", "cancelled", "blocked"],
                    "description": "New status for the goal"
                }
            },
            "required": ["goal_id", "status"]
        }

    async def execute(
            self,
            session: AsyncSession,
            context: dict[str, Any],
            **kwargs
    ) -> dict[str, Any]:
        """Execute goal status update."""
        goal_id_str = kwargs.get("goal_id")
        status_str = kwargs.get("status")

        try:
            goal_id = UUID(goal_id_str)
            status = GoalStatus(status_str)
        except ValueError as e:
            return {"error": f"Invalid input: {str(e)}"}

        goal_service = GoalService(session)
        goal = await goal_service.update_goal_status(goal_id, status)

        if not goal:
            return {"error": f"Goal not found: {goal_id_str}"}

        return {
            "success": True,
            "goal_id": str(goal.id),
            "title": goal.title,
            "status": goal.status.value,
            "updated_at": goal.updated_at.isoformat()
        }


class UpdateGoalTool(BaseTool):
    """Tool for updating goal title/description."""

    @property
    def name(self) -> str:
        return "update_goal"

    @property
    def description(self) -> str:
        return "Update goal title and/or description"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "goal_id": {
                    "type": "string",
                    "description": "Goal UUID to update"
                },
                "title": {
                    "type": "string",
                    "description": "New goal title (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New goal description (optional)"
                }
            },
            "required": ["goal_id"]
        }

    async def execute(
            self,
            session: AsyncSession,
            context: dict[str, Any],
            **kwargs
    ) -> dict[str, Any]:
        """Execute goal update."""
        goal_id_str = kwargs.get("goal_id")
        title = kwargs.get("title")
        description = kwargs.get("description")

        if not title and not description:
            return {"error": "Either title or description must be provided"}

        try:
            goal_id = UUID(goal_id_str)
        except ValueError:
            return {"error": f"Invalid goal_id format: {goal_id_str}"}

        goal_service = GoalService(session)
        goal = await goal_service.update_goal(
            goal_id=goal_id,
            title=title,
            description=description
        )

        if not goal:
            return {"error": f"Goal not found: {goal_id_str}"}

        return {
            "success": True,
            "goal_id": str(goal.id),
            "title": goal.title,
            "description": goal.description,
            "updated_at": goal.updated_at.isoformat()
        }


class DeleteGoalTool(BaseTool):
    """Tool for deleting a goal."""

    @property
    def name(self) -> str:
        return "delete_goal"

    @property
    def description(self) -> str:
        return "Delete a goal and all its sub-goals (cascade)"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "goal_id": {
                    "type": "string",
                    "description": "Goal UUID to delete"
                }
            },
            "required": ["goal_id"]
        }

    async def execute(
            self,
            session: AsyncSession,
            context: dict[str, Any],
            **kwargs
    ) -> dict[str, Any]:
        """Execute goal deletion."""
        goal_id_str = kwargs.get("goal_id")

        try:
            goal_id = UUID(goal_id_str)
        except ValueError:
            return {"error": f"Invalid goal_id format: {goal_id_str}"}

        goal_service = GoalService(session)
        deleted = await goal_service.delete_goal(goal_id)

        if not deleted:
            return {"error": f"Goal not found: {goal_id_str}"}

        return {
            "success": True,
            "goal_id": goal_id_str,
            "message": "Goal and all sub-goals deleted successfully"
        }


class LinkGoalTool(BaseTool):
    """Tool for linking/unlinking goals."""

    @property
    def name(self) -> str:
        return "link_goal"

    @property
    def description(self) -> str:
        return "Link a goal to a parent goal or make it independent"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "goal_id": {
                    "type": "string",
                    "description": "Goal UUID to link"
                },
                "parent_id": {
                    "type": "string",
                    "description": "Parent goal UUID (null/empty to make independent)"
                }
            },
            "required": ["goal_id"]
        }

    async def execute(
            self,
            session: AsyncSession,
            context: dict[str, Any],
            **kwargs
    ) -> dict[str, Any]:
        """Execute goal linking."""
        goal_id_str = kwargs.get("goal_id")
        parent_id_str = kwargs.get("parent_id")

        try:
            goal_id = UUID(goal_id_str)
        except ValueError:
            return {"error": f"Invalid goal_id format: {goal_id_str}"}

        parent_id = None
        if parent_id_str:
            try:
                parent_id = UUID(parent_id_str)
            except ValueError:
                return {"error": f"Invalid parent_id format: {parent_id_str}"}

        goal_service = GoalService(session)
        goal = await goal_service.link_goal_to_parent(goal_id, parent_id)

        if not goal:
            return {"error": f"Goal not found: {goal_id_str}"}

        return {
            "success": True,
            "goal_id": str(goal.id),
            "title": goal.title,
            "parent_id": str(goal.parent_id) if goal.parent_id else None,
            "message": "Goal linked successfully" if parent_id else "Goal is now independent"
        }