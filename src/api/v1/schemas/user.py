from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base User schema with common fields."""
    apple_id: str
    name: str | None = None
    email: str | None = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserNameUpdate(BaseModel):
    """Schema for updating user name."""
    name: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
