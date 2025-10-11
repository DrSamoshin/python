"""
Request logging middleware.

Logs all incoming requests and outgoing responses with metadata:
- Request ID for distributed tracing
- Request method, URL, client IP
- Response status code, processing time
- Adds X-Request-ID header to responses for client-side tracking
"""

import time
import uuid
import logging
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Features:
    - Generates unique Request ID (UUID) for each request
    - Logs request metadata (method, URL, client IP)
    - Logs response metadata (status code, processing duration)
    - Adds X-Request-ID header to responses for tracing
    - Skips logging for health check endpoints to reduce noise
    - Stores request_id in request.state for use in route handlers

    Usage in route handlers:
        @app.get("/users")
        async def get_users(request: Request):
            request_id = request.state.request_id
            logger.info(f"Fetching users", extra={"request_id": request_id})
    """

    # Endpoints to skip logging (health checks, metrics)
    SKIP_PATHS = {"/health/", "/metrics", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        """
        Process request with logging.

        Flow:
        1. Generate unique Request ID
        2. Log incoming request with metadata
        3. Store request_id in request.state
        4. Process request
        5. Calculate duration
        6. Log response with status and timing
        7. Add X-Request-ID header to response
        """
        # Skip logging for health checks and docs
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Store in request state for use in route handlers
        request.state.request_id = request_id

        # Log incoming request
        self.logger.info(
            "Incoming request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate processing duration
        duration = time.time() - start_time

        # Log response
        self.logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
        )

        # Add Request-ID to response headers for client-side tracking
        response.headers["X-Request-ID"] = request_id

        # Add processing time header (useful for monitoring)
        response.headers["X-Process-Time"] = f"{duration:.4f}"

        return response


def setup_logging_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestLoggingMiddleware) # type: ignore[arg-type]
