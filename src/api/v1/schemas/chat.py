from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from src.api.v1.schemas.message import MessageSchema


class ChatSchema(BaseModel):
    """Schema for chat in API responses."""
    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatCreate(BaseModel):
    """Schema for creating a new chat."""
    title: str | None = None


class ChatWithMessages(ChatSchema):
    """Chat with messages included."""
    messages: list[MessageSchema] = []

    model_config = ConfigDict(from_attributes=True)
