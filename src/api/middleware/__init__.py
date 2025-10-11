"""
Middleware configuration module.

Central place for setting up all application middleware.
Middleware are executed in the order they are added:
Request → CORS → [other middleware] → Route Handler → Response
"""

from fastapi import FastAPI
from src.api.middleware.cors import setup_cors
from src.api.middleware.logging import setup_logging_middleware


def setup_middlewares(app: FastAPI) -> None:
    """
    Configure all middleware for the application.

    Order matters! Middleware execute in reverse order:
    - CORS first (handles preflight requests)
    - Logging second (captures timing for all requests)

    Note: Rate limiting is handled at the reverse proxy level (Nginx/Caddy)
    """
    setup_cors(app)
    setup_logging_middleware(app)

    # Future middleware to add:
    # setup_error_handler(app)
    # setup_security_headers(app)


__all__ = ["setup_middlewares"]