"""
    Auth service layer.
    Handles JWT token generation and validation.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import JWTError, jwt

from src.api.core.configs import settings
from src.api.exceptions import UnauthorizedError


class AuthService:
    """Service for JWT token operations."""

    @staticmethod
    def create_access_token(user_id: UUID) -> str:
        """Create access token for user."""
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_refresh_token(user_id: UUID) -> str:
        """Create refresh token for user."""
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> UUID:
        """
        Verify token and return user_id.
        Raises UnauthorizedError if token is invalid.
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            user_id: str | None = payload.get("sub")
            token_type_from_payload: str | None = payload.get("type")

            if user_id is None:
                raise UnauthorizedError("Invalid token: missing user ID")

            if token_type_from_payload != token_type:
                raise UnauthorizedError(f"Invalid token type: expected {token_type}")

            return UUID(user_id)
        except JWTError as e:
            raise UnauthorizedError(f"Invalid token: {str(e)}")

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode token without verification (for debugging)."""
        try:
            return jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
        except JWTError as e:
            raise UnauthorizedError(f"Invalid token: {str(e)}")
