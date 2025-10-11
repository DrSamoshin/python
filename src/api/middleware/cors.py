"""
CORS (Cross-Origin Resource Sharing) Middleware.

This middleware adds CORS headers to server responses,
allowing browsers to make requests from different domains.

How it works:
1. Browser sends a preflight request (OPTIONS) before the main request
2. Middleware adds Access-Control-Allow-* headers to the response
3. Browser checks headers and allows/blocks the main request
"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.api.core.configs import settings


def setup_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,  # allow cookies/Authorization header
        allow_methods=["*"],  # all methods: GET, POST, PUT, DELETE, PATCH...
        allow_headers=["*"],  # main headers
    )