from __future__ import annotations # По умолчанию, Python вычисляет аннотации сразу при загрузке модуля. Но иногда тебе нужно сослаться на класс, который объявлен позже или даже на сам класс (self type).

from fastapi import APIRouter
from src.api.v1.routers import health_router, users_router, chat_ws_router, chat_router, admin_router


api_router = APIRouter(prefix="/v1")
api_router.include_router(health_router)
api_router.include_router(users_router)
api_router.include_router(chat_ws_router)
api_router.include_router(chat_router)
api_router.include_router(admin_router)


__all__ = ["api_router"]
