"""Base WebSocket handler with common logic."""

from abc import ABC, abstractmethod
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from uuid import UUID
import logging
import json

from src.api.v1.websocket.connection_manager import ConnectionManager
from src.api.services import ChatSessionService
from src.api.v1.schemas import MessageSchema

logger = logging.getLogger(__name__)


class BaseWebSocketHandler(ABC):
    """Base class for WebSocket handlers with common logic."""

    def __init__(
            self,
            websocket: WebSocket,
            session: AsyncSession,
            redis: Redis,
            connection_manager: ConnectionManager
    ):
        self.websocket = websocket
        self.session = session
        self.redis = redis
        self.connection_manager = connection_manager
        self.chat_session_service = ChatSessionService(session, redis)

        # Will be set by subclasses in setup_session()
        self.user_id: UUID | None = None
        self.chat_id: UUID | None = None

    async def handle_connection(self):
        """Main handler for WebSocket connection lifecycle."""
        try:
            # Setup session (create demo user, validate auth, etc.)
            await self.setup_session()

            # Connect WebSocket
            await self.connection_manager.connect(
                self.websocket,
                self.chat_id,
                self.user_id
            )

            # Load initial chat history
            history = await self.chat_session_service.load_initial_history(self.chat_id)
            logger.info(f"WebSocket session started: user={self.user_id}, chat={self.chat_id}")

            # Main message loop
            await self.message_loop()

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for chat {self.chat_id}")

        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
            await self.send_error("Internal server error")

        finally:
            # Cleanup (delete demo user, close connections, etc.)
            await self.cleanup_session()

            # Disconnect WebSocket
            if self.chat_id:
                await self.connection_manager.disconnect(self.websocket, self.chat_id)

    @abstractmethod
    async def setup_session(self):
        """
        Setup session before handling messages.

        For demo: create temporary user and chat
        For normal: validate existing user and chat

        Must set self.user_id and self.chat_id
        """
        pass

    @abstractmethod
    async def cleanup_session(self):
        """
        Cleanup session after connection closes.

        For demo: delete temporary user
        For normal: nothing to cleanup
        """
        pass

    async def message_loop(self):
        """Main loop for receiving and processing messages."""
        while True:
            # Receive message from client
            data = await self.websocket.receive_text()

            try:
                message_data = json.loads(data)
                await self.handle_message(message_data)

            except json.JSONDecodeError:
                await self.send_error("Invalid JSON format")

            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)
                await self.send_error("Failed to process message")

    async def handle_message(self, data: dict):
        """
        Handle incoming message from user.
        Expected format: {"type": "message", "content": "text"}
        """
        message_type = data.get("type")

        if message_type == "message":
            await self.handle_user_message(data)
        elif message_type == "ping":
            await self.handle_ping()
        else:
            await self.send_error(f"Unknown message type: {message_type}")

    async def handle_user_message(self, data: dict):
        """Process user message and generate assistant response."""
        content = data.get("content", "").strip()

        if not content:
            await self.send_error("Message content cannot be empty")
            return

        try:
            # Process message through ChatSessionService
            result = await self.chat_session_service.process_user_message(
                chat_id=self.chat_id,
                content=content,
                user_id=self.user_id
            )

            # Send messages to client
            await self.send_message(result.user_message)
            await self.send_message(result.assistant_message)

        except Exception as e:
            logger.error(f"Error processing user message: {e}", exc_info=True)
            await self.send_error("Sorry, I couldn't process your message. Please try again.")

    async def send_message(self, message):
        """Send message to client."""
        message_schema = MessageSchema.model_validate(message)

        await self.websocket.send_json({
            "type": "message",
            "data": message_schema.model_dump(mode='json')
        })

    async def send_error(self, error: str):
        """Send error message to client."""
        await self.websocket.send_json({
            "type": "error",
            "error": error
        })

    async def handle_ping(self):
        """Handle ping message (keep-alive)."""
        await self.websocket.send_json({"type": "pong"})