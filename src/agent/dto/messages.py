"""Message DTOs for Agent system."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class AgentMessage:
    """Simple message DTO for Agent."""
    role: Literal["user", "assistant", "system"]
    content: str


@dataclass
class AgentRequest:
    """Request to Agent with chat history."""
    chat_history: list[AgentMessage]
    user_message: AgentMessage


@dataclass
class AgentResponse:
    """Response from Agent."""
    content: str
    # TODO: Add tool_calls when we implement tools
    # tool_calls: list[ToolCall] | None = None