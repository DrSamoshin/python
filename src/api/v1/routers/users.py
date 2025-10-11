"""Users router with CRUD endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.database import get_db
from src.api.v1.schemas import SuccessResponse
from src.api.v1.schemas.user import UserCreate, UserUpdate, UserResponse
from src.api.services.user_service import UserService

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[UserResponse])
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[UserResponse]:
    """Create a new user."""
    service = UserService(db)
    user = await service.create_user(name=user_data.name, email=user_data.email)
    logger.info(f"User created: {user.id}")
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[UserResponse]:
    """Get user by ID."""
    service = UserService(db)
    user = await service.get_user(user_id)
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.patch("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user_name(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[UserResponse]:
    """Update user name."""
    service = UserService(db)
    user = await service.update_user_name(user_id, user_data.name)
    logger.info(f"User updated: {user.id}")
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete user."""
    service = UserService(db)
    await service.delete_user(user_id)
    logger.info(f"User deleted: {user_id}")
