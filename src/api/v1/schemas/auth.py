"""Auth schemas for token operations."""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Response model for token generation."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str
