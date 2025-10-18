from fastapi import WebSocket
from typing import Dict, Set
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for chat."""

    def __init__(self):
        # Dict[chat_id, Set[WebSocket]]
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        # Dict[WebSocket, user_id]
        self.websocket_users: Dict[WebSocket, UUID] = {}

    async def connect(self, websocket: WebSocket, chat_id: UUID, user_id: UUID):
        """Accept WebSocket connection and register it."""
        await websocket.accept()

        # Add to chat room
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()
        self.active_connections[chat_id].add(websocket)

        # Track user
        self.websocket_users[websocket] = user_id

        logger.info(f"User {user_id} connected to chat {chat_id}")

    async def disconnect(self, websocket: WebSocket, chat_id: UUID):
        """Remove WebSocket connection."""
        # Remove from chat room
        if chat_id in self.active_connections:
            self.active_connections[chat_id].discard(websocket)

            # Cleanup empty chat rooms
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

        # Remove user tracking
        user_id = self.websocket_users.pop(websocket, None)

        logger.info(f"User {user_id} disconnected from chat {chat_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket connection."""
        await websocket.send_json(message)

    async def broadcast_to_chat(self, message: dict, chat_id: UUID):
        """Broadcast message to all connections in a chat room."""
        if chat_id in self.active_connections:
            disconnected = set()

            for connection in self.active_connections[chat_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to connection: {e}")
                    disconnected.add(connection)

            # Cleanup disconnected
            for connection in disconnected:
                await self.disconnect(connection, chat_id)

    def get_user_id(self, websocket: WebSocket) -> UUID | None:
        """Get user_id for a WebSocket connection."""
        return self.websocket_users.get(websocket)
