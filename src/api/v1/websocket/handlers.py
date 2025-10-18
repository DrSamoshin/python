from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from uuid import UUID
import logging
import json

from src.api.v1.websocket.connection_manager import ConnectionManager
from src.api.services import ChatService, MessageService
from src.models import MessageRole
from src.api.v1.schemas import MessageSchema
from src.api.exceptions import NotFoundException, ForbiddenException

logger = logging.getLogger(__name__)


class ChatWebSocketHandler:
    """Handler for chat WebSocket events."""

    def __init__(
            self,
            websocket: WebSocket,
            chat_id: UUID,
            user_id: UUID,
            session: AsyncSession,
            redis: Redis,
            connection_manager: ConnectionManager
    ):
        self.websocket = websocket
        self.chat_id = chat_id
        self.user_id = user_id
        self.session = session
        self.redis = redis
        self.connection_manager = connection_manager

        # Services
        self.chat_service = ChatService(session)
        self.message_service = MessageService(session, redis)

    async def handle_connection(self):
        """Main handler for WebSocket connection lifecycle."""
        try:
            # Verify user has access to this chat
            await self.verify_access()

            # Connect WebSocket
            await self.connection_manager.connect(
                self.websocket,
                self.chat_id,
                self.user_id
            )

            # Send chat history
            await self.send_history()

            # Main message loop
            await self.message_loop()

        except (NotFoundException, ForbiddenException) as e:
            logger.warning(f"Access denied for user {self.user_id} to chat {self.chat_id}: {e}")
            await self.websocket.close(code=1008, reason=str(e))

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for chat {self.chat_id}")

        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
            await self.send_error("Internal server error")

        finally:
            await self.connection_manager.disconnect(self.websocket, self.chat_id)

    async def verify_access(self):
        """Verify user has access to the chat."""
        await self.chat_service.get_chat(self.chat_id, self.user_id)

    async def send_history(self):
        """Send chat history to the connected client."""
        try:
            messages = await self.message_service.get_chat_history(self.chat_id)

            await self.websocket.send_json({
                "type": "history",
                "messages": [msg.model_dump(mode='json') for msg in messages]
            })

            logger.info(f"Sent {len(messages)} messages history to user {self.user_id}")

        except Exception as e:
            logger.error(f"Error sending history: {e}")
            await self.send_error("Failed to load chat history")

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

        # Save user message
        user_message = await self.message_service.create_message(
            chat_id=self.chat_id,
            role=MessageRole.USER,
            content=content
        )

        # Send confirmation to user
        await self.send_message(user_message)

        # TODO: Here you will integrate your RAG agent
        # For now, simple echo response
        assistant_content = await self.generate_assistant_response(content)

        # Save assistant message
        assistant_message = await self.message_service.create_message(
            chat_id=self.chat_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content
        )

        # Send assistant response
        await self.send_message(assistant_message)

    async def generate_assistant_response(self, user_content: str) -> str:
        """
        Generate assistant response using RAG agent.
        TODO: Replace with actual RAG implementation.
        """
        # Placeholder - simple echo for now
        return f"Echo: {user_content}"

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
        """Handle ping for keeping connection alive."""
        await self.websocket.send_json({"type": "pong"})
