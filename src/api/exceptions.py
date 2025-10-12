"""
    Application exceptions with HTTP status codes.
    All custom exceptions inherit from AppException.
"""

from typing import Optional


class AppException(Exception):
    """Base exception for all application errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class UserNotFoundError(AppException):
    """Raised when user is not found."""
    
    def __init__(self, message: str = "User not found"):
        super().__init__(
            message=message,
            status_code=404,
            error_code="USER_NOT_FOUND"
        )


class UserAlreadyExistsError(AppException):
    """Raised when trying to create user with existing email."""
    
    def __init__(self, message: str = "User already exists"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="USER_ALREADY_EXISTS"
        )


class ValidationError(AppException):
    """Raised for validation errors."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR"
        )


class UnauthorizedError(AppException):
    """Raised when authentication fails or token is invalid."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED"
        )
