from __future__ import annotations

from src.api.v1.routers.health import router as health_router
from src.api.v1.routers.users import router as users_router

__all__: list[str] = [
    "health_router",
    "users_router",
]