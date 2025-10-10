from fastapi import FastAPI
from src.api.v1 import api_router

def create_app() -> FastAPI:
    app = FastAPI(title="test_app", version="0.1.0")
    app.include_router(api_router)
    return app

fastapi_app = create_app()

__all__ = ["fastapi_app", "create_app"]
