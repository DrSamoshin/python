from fastapi import APIRouter, WebSocket, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from uuid import UUID

from src.api.core.database import get_db
from src.api.core.redis_client import get_redis
from src.api.dependencies.auth import get_current_user_ws
from src.api.v1.websocket import ConnectionManager, ChatWebSocketHandler
from src.api.v1.websocket.demo_handler import DemoWebSocketHandler
from src.models import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Global connection manager (singleton)
connection_manager = ConnectionManager()


@router.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """Simple test endpoint."""
    await websocket.accept()
    await websocket.send_text("Hello from test endpoint!")
    await websocket.close()


@router.websocket("/ws/demo")
async def websocket_demo_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for demo chat with temporary users.

    Connection URL: ws://localhost:8080/v1/chat/ws/demo
    No authorization required.

    On connection:
    - Creates temporary demo user (apple_id: demo_<uuid>)
    - Creates chat for demo user
    - Works like normal chat

    On disconnect:
    - Deletes demo user and all associated data (cascade)

    Message format (client -> server):
    {
        "type": "message",
        "content": "user message text"
    }

    Message format (server -> client):
    {
        "type": "message",
        "data": {
            "id": "uuid",
            "chat_id": "uuid",
            "role": "user|assistant|system",
            "content": "message text",
            "created_at": "2025-10-25T10:00:00"
        }
    }

    Error format:
    {
        "type": "error",
        "error": "error message"
    }
    """
    # Get dependencies manually
    from src.api.core.database import get_db
    from src.api.core.redis_client import get_redis

    db = None
    redis = None

    try:
        async for session in get_db():
            db = session
            break

        redis = await get_redis()

        # Create demo handler (no auth required)
        handler = DemoWebSocketHandler(
            websocket=websocket,
            session=db,
            redis=redis,
            connection_manager=connection_manager
        )

        # Handle connection (this will accept WebSocket internally)
        await handler.handle_connection()

    except Exception as e:
        logger.error(f"Demo WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@router.websocket("/ws/{chat_id}")
async def websocket_chat_endpoint(
        websocket: WebSocket,
        chat_id: UUID,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    """
    WebSocket endpoint for real-time chat.

    Connection URL: ws://localhost:8080/api/v1/chat/ws/{chat_id}
    Authorization: Pass JWT token in Authorization header: "Bearer <token>"

    Message format (client -> server):
    {
        "type": "message",
        "content": "user message text"
    }

    Message format (server -> client):
    {
        "type": "message",
        "data": {
            "id": "uuid",
            "chat_id": "uuid",
            "role": "user|assistant|system",
            "content": "message text",
            "created_at": "2025-10-18T10:00:00"
        }
    }

    History format (server -> client on connect):
    {
        "type": "history",
        "messages": [...]
    }

    Error format:
    {
        "type": "error",
        "error": "error message"
    }
    """
    try:
        # Get authorization header from WebSocket headers
        authorization = websocket.headers.get("authorization")

        # Authenticate user
        user: User = await get_current_user_ws(authorization, db)

        # Create handler
        handler = ChatWebSocketHandler(
            websocket=websocket,
            chat_id=chat_id,
            user_id=user.id,
            session=db,
            redis=redis,
            connection_manager=connection_manager
        )

        # Handle connection
        await handler.handle_connection()

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
