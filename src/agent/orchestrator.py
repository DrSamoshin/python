"""Agent Orchestrator - coordinates LLM, Tools, and RAG."""

import logging
from src.agent.llm.openai_client import OpenAIClient
from src.agent.tools import ToolRegistry
from src.agent.tools.goal_tools import (
    CreateGoalTool,
    ListGoalsTool,
    UpdateGoalStatusTool,
    UpdateGoalTool,
    DeleteGoalTool,
    LinkGoalTool
)
from src.agent.dto import (
    AgentMessage,
    AgentRequest,
    AgentResponse,
    ToolCall,
    ToolCallMetadata
)
from src.agent.exceptions import LLMError, LLMAuthenticationError, LLMRateLimitError

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Main coordinator for Agent system with error handling."""

    def __init__(self, tool_registry: ToolRegistry | None = None):
        self.llm_client = OpenAIClient()
        self.tool_registry = tool_registry or ToolRegistry()

        # Register goal management tools
        self._register_goal_tools()

        # TODO: context_builder

    def _register_goal_tools(self):
        """Register goal management tools."""
        self.tool_registry.register(CreateGoalTool())
        self.tool_registry.register(ListGoalsTool())
        self.tool_registry.register(UpdateGoalStatusTool())
        self.tool_registry.register(UpdateGoalTool())
        self.tool_registry.register(DeleteGoalTool())
        self.tool_registry.register(LinkGoalTool())

    async def process(self, request: AgentRequest, session=None) -> AgentResponse:
        """
        Process user message through LLM with tool execution support.

        Args:
            request: AgentRequest with chat history and user message

        Returns:
            AgentResponse with generated content and optional tool metadata
        """
        try:
            # Combine history + current message
            all_messages = request.chat_history + [request.user_message]

            # Get tool schemas if tools are registered
            tools = None
            if self.tool_registry.get_all_tools():
                tools = self.tool_registry.get_openai_schemas()

            # First LLM call
            response = await self.llm_client.chat_completion(
                messages=all_messages,
                system_message="You are a helpful assistant.",
                tools=tools
            )

            # Check if LLM wants to call tools
            assistant_message = response.choices[0].message

            if assistant_message.tool_calls:
                # Execute tool calls
                logger.info(f"LLM requested {len(assistant_message.tool_calls)} tool calls")
                tool_metadata = await self._execute_tool_calls(
                    all_messages,
                    assistant_message,
                    session,
                    request.chat_id
                )

                # Return response with tool metadata
                return AgentResponse(
                    content=tool_metadata["final_content"],
                    tool_metadata=ToolCallMetadata(
                        tool_calls=tool_metadata["tool_calls"],
                        tool_results=tool_metadata["tool_results"]
                    )
                )

            # No tools - return simple response
            return AgentResponse(content=assistant_message.content or "")

        except LLMAuthenticationError as e:
            logger.error(f"LLM authentication error: {e}")
            return AgentResponse(
                content="Configuration error: Invalid OpenAI API key. Please contact support."
            )

        except LLMRateLimitError as e:
            logger.error(f"LLM rate limit error: {e}")
            return AgentResponse(
                content="Too many requests. Please wait a moment and try again."
            )

        except LLMError as e:
            logger.error(f"LLM error: {e}")
            return AgentResponse(
                content=f"Sorry, I encountered an error: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Unexpected error in AgentOrchestrator: {e}", exc_info=True)
            return AgentResponse(
                content="An unexpected error occurred. Please try again."
            )

    async def _execute_tool_calls(
            self,
            messages: list[AgentMessage],
            assistant_message,
            session,
            chat_id
    ) -> dict:
        """
        Execute tool calls and get final LLM response.

        Args:
            messages: Message history before tool calls
            assistant_message: Assistant message with tool_calls

        Returns:
            Dict with final_content, tool_calls, and tool_results
        """
        # Convert OpenAI tool_calls to ToolCall DTOs
        tool_calls = [
            ToolCall(
                id=tc.id,
                type=tc.type,
                function={"name": tc.function.name, "arguments": tc.function.arguments}
            )
            for tc in assistant_message.tool_calls
        ]

        # Execute tools
        context = {"chat_id": chat_id}
        tool_results = await self.tool_registry.execute_tool_calls(
            tool_calls,
            session,
            context
        )

        # Build messages for second LLM call
        # Combine tool_calls and tool_results in ONE AgentMessage
        messages_with_tools = messages + [
            AgentMessage(
                role="assistant",
                content=assistant_message.content,
                tool_call_data={
                    "tool_calls": [tc.model_dump() for tc in tool_calls],
                    "tool_results": [tr.model_dump() for tr in tool_results]
                }
            )
        ]

        # Second LLM call with tool results
        final_response = await self.llm_client.chat_completion(
            messages=messages_with_tools,
            system_message="You are a helpful assistant."
        )

        final_content = final_response.choices[0].message.content or ""

        return {
            "final_content": final_content,
            "tool_calls": [tc.model_dump() for tc in tool_calls],
            "tool_results": [tr.model_dump() for tr in tool_results]
        }


