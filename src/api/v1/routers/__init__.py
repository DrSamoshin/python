from __future__ import annotations

from src.api.v1.routers.health import router as health_router
from src.api.v1.routers.users import router as users_router
from src.api.v1.routers.chat_ws import router as chat_ws_router
from src.api.v1.routers.chat import router as chat_router
from src.api.v1.routers.admin import router as admin_router

__all__: list[str] = [
    "health_router",
    "users_router",
    "chat_ws_router",
    "chat_router",
    "admin_router",
]