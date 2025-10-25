"""Base class for Agent tools."""

from abc import ABC, abstractmethod
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession


class BaseTool(ABC):
    """Base class for all Agent tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (must match OpenAI function name)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """
        JSON Schema for tool parameters.

        Example:
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Goal title"},
                "description": {"type": "string", "description": "Goal description"}
            },
            "required": ["title"]
        }
        """
        pass

    @abstractmethod
    async def execute(
            self,
            session: AsyncSession,
            context: dict[str, Any],
            **kwargs
    ) -> dict[str, Any]:
        """
        Execute the tool with given parameters.

        Args:
            session: Database session for repository access
            context: Execution context (chat_id, user_id, etc.)
            **kwargs: Tool parameters from LLM

        Returns:
            Result dictionary that will be sent back to LLM
        """
        pass

    def to_openai_schema(self) -> dict[str, Any]:
        """
        Convert tool to OpenAI function schema.

        Returns:
            OpenAI function calling schema
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }