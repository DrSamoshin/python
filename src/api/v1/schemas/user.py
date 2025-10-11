from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base User schema with common fields."""
    name: str
    email: str


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating user name."""
    name: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
