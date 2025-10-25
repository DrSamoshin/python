"""Tool Registry for managing and executing tools."""

import json
import logging
from typing import Any
from src.agent.tools.base import BaseTool
from src.agent.dto import ToolCall, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing Agent tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> BaseTool | None:
        """Get tool by name."""
        return self._tools.get(name)

    def get_all_tools(self) -> list[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_openai_schemas(self) -> list[dict[str, Any]]:
        """
        Get OpenAI function schemas for all registered tools.

        Returns:
            List of OpenAI function calling schemas
        """
        return [tool.to_openai_schema() for tool in self._tools.values()]

    async def execute_tool_call(
            self,
            tool_call: ToolCall,
            session,
            context: dict[str, Any]
    ) -> ToolResult:
        """
        Execute a single tool call.

        Args:
            tool_call: ToolCall from LLM

        Returns:
            ToolResult with execution result
        """
        function_name = tool_call.function.get("name")
        arguments_str = tool_call.function.get("arguments", "{}")

        # Get tool
        tool = self.get_tool(function_name)
        if not tool:
            error_result = {
                "error": f"Tool '{function_name}' not found",
                "available_tools": list(self._tools.keys())
            }
            logger.error(f"Tool not found: {function_name}")
            return ToolResult(
                tool_call_id=tool_call.id,
                name=function_name,
                result=error_result
            )

        # Parse arguments
        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError as e:
            error_result = {"error": f"Invalid JSON arguments: {str(e)}"}
            logger.error(f"Invalid JSON in tool call {tool_call.id}: {e}")
            return ToolResult(
                tool_call_id=tool_call.id,
                name=function_name,
                result=error_result
            )

        # Execute tool
        try:
            logger.info(f"Executing tool '{function_name}' with args: {arguments}")
            result = await tool.execute(session=session, context=context, **arguments)
            logger.info(f"Tool '{function_name}' executed successfully")

            return ToolResult(
                tool_call_id=tool_call.id,
                name=function_name,
                result=result
            )

        except Exception as e:
            error_result = {
                "error": f"Tool execution failed: {str(e)}",
                "tool": function_name
            }
            logger.error(f"Tool execution error in '{function_name}': {e}", exc_info=True)
            return ToolResult(
                tool_call_id=tool_call.id,
                name=function_name,
                result=error_result
            )

    async def execute_tool_calls(
            self,
            tool_calls: list[ToolCall],
            session,
            context: dict[str, Any]
    ) -> list[ToolResult]:
        """
        Execute multiple tool calls.

        Args:
            tool_calls: List of ToolCall objects from LLM
            session: Database session
            context: Execution context (chat_id, etc.)

        Returns:
            List of ToolResult objects
        """
        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool_call(tool_call, session, context)
            results.append(result)

        return results