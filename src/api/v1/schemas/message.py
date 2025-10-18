from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from src.models import MessageRole


class MessageSchema(BaseModel):
    """Schema for message in cache and API responses."""
    id: UUID
    chat_id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    """Schema for creating a new message (from user)."""
    content: str
