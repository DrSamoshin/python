"""Users router with CRUD endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.database import get_db
from src.api.v1.schemas import SuccessResponse
from src.api.v1.schemas.user import UserCreate, UserNameUpdate, UserResponse
from src.api.v1.schemas.auth import TokenResponse, RefreshTokenRequest
from src.api.services.user_service import UserService
from src.api.services.auth_service import AuthService
from src.api.dependencies.auth import get_current_user
from src.models.user import User

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=status.HTTP_200_OK)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user and return with auth tokens."""
    user_service = UserService(db)
    auth_service = AuthService()

    user = await user_service.create_user_with_apple_id(
        apple_id=user_data.apple_id,
        name=user_data.name,
        email=user_data.email,
        is_active=True
    )
    logger.info(f"User created: {user.id}")

    # Generate tokens
    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)

    return SuccessResponse(data={
        "user": UserResponse.model_validate(user),
        "tokens": TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    })


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SuccessResponse[UserResponse]:
    """Get user by ID. Requires authentication."""
    service = UserService(db)
    user = await service.get_user(user_id)
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.patch("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user_name(
    user_id: UUID,
    user_data: UserNameUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SuccessResponse[UserResponse]:
    """Update user name. Requires authentication."""
    service = UserService(db)
    user = await service.update_user_name(user_id, user_data.name)
    logger.info(f"User updated: {user.id}")
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete user. Requires authentication."""
    service = UserService(db)
    await service.delete_user(user_id)
    logger.info(f"User deleted: {user_id}")


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[TokenResponse]:
    """Refresh access token using refresh token."""
    auth_service = AuthService()

    # Verify refresh token and get user_id
    user_id = auth_service.verify_token(token_data.refresh_token, token_type="refresh")

    # Generate new tokens
    access_token = auth_service.create_access_token(user_id)
    refresh_token = auth_service.create_refresh_token(user_id)

    return SuccessResponse(data=TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    ))
