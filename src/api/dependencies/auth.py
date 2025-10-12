"""Authentication dependencies."""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.core.database import get_db
from src.api.services.auth_service import AuthService
from src.api.services.user_service import UserService
from src.models.user import User
from src.api.exceptions import UnauthorizedError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate access token and return current user.

    Expects Authorization header in format: "Bearer <token>"
    Raises UnauthorizedError if token is invalid or user not found.
    """
    # Extract token from credentials
    token = credentials.credentials

    # Verify token and get user_id
    auth_service = AuthService()
    user_id = auth_service.verify_token(token, token_type="access")

    # Get user from database
    user_service = UserService(db)
    try:
        user = await user_service.get_user(user_id)
    except Exception:
        raise UnauthorizedError("User not found or token is invalid")

    # Check if user is active
    if not user.is_active:
        raise UnauthorizedError("User is not active")

    return user
