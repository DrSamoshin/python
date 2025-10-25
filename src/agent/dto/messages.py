"""Message DTOs for Agent system."""

from pydantic import BaseModel, Field
from typing import Literal, Any
from uuid import UUID


class AgentMessage(BaseModel):
    """Simple message DTO for Agent."""
    role: Literal["user", "assistant", "system"]
    content: str | None = None
    tool_call_data: dict | None = None


class AgentRequest(BaseModel):
    """Request to Agent with chat history."""
    chat_history: list[AgentMessage]
    user_message: AgentMessage
    chat_id: UUID  # Chat UUID for tools context


class ToolCall(BaseModel):
    """OpenAI tool call structure."""
    id: str
    type: str = "function"
    function: dict[str, Any]  # {"name": str, "arguments": str}


class ToolResult(BaseModel):
    """Tool execution result."""
    tool_call_id: str
    name: str
    result: dict[str, Any]  # Actual result from tool execution


class ToolCallMetadata(BaseModel):
    """Metadata about tool calls executed during agent processing."""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Response from Agent."""
    content: str
    tool_metadata: ToolCallMetadata | None = None