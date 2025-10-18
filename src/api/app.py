from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1 import api_router
from src.api.core.configs import settings
from src.api.middleware import setup_middlewares
from src.api.exception_handlers import setup_exception_handlers
from src.api.core.database import close_db
from src.api.core.redis_client import close_redis

import logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"FastAPI app started in '{settings.env}' environment")
    yield
    # Shutdown
    logger.info("Closing database connections...")
    await close_db()
    await close_redis()
    logger.info("FastAPI app shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        lifespan=lifespan
    )
    setup_exception_handlers(app)
    setup_middlewares(app)
    app.include_router(api_router)
    return app


fastapi_app = create_app()


__all__ = ["fastapi_app", "create_app"]
