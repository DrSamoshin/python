from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from uuid import UUID
import logging
import asyncio
from datetime import datetime

from src.api.v1.websocket.base_handler import BaseWebSocketHandler
from src.api.v1.websocket.connection_manager import ConnectionManager
from src.api.services import ChatService
from src.api.exceptions import NotFoundException, ForbiddenException
from src.api.core.configs import settings

logger = logging.getLogger(__name__)


class ChatWebSocketHandler(BaseWebSocketHandler):
    """Handler for authenticated chat WebSocket with idle timeout."""

    def __init__(
            self,
            websocket: WebSocket,
            chat_id: UUID,
            user_id: UUID,
            session: AsyncSession,
            redis: Redis,
            connection_manager: ConnectionManager
    ):
        super().__init__(websocket, session, redis, connection_manager)
        self.chat_id = chat_id
        self.user_id = user_id
        self.chat_service = ChatService(session)

        # Idle timeout tracking
        self.last_activity = datetime.now()
        self.idle_check_task = None

    async def setup_session(self):
        """Verify user has access to the chat."""
        await self.chat_service.get_chat(self.chat_id, self.user_id)

    async def cleanup_session(self):
        """Cancel idle timeout checker."""
        if self.idle_check_task:
            self.idle_check_task.cancel()
            try:
                await self.idle_check_task
            except asyncio.CancelledError:
                pass

    async def handle_connection(self):
        """Extended connection handler with idle timeout."""
        try:
            # Setup and connect
            await self.setup_session()
            await self.connection_manager.connect(
                self.websocket,
                self.chat_id,
                self.user_id
            )

            # Load history
            history = await self.chat_session_service.load_initial_history(self.chat_id)
            logger.info(f"WebSocket session started: user={self.user_id}, chat={self.chat_id}, messages={len(history)}")

            # Start idle timeout checker
            self.idle_check_task = asyncio.create_task(self.check_idle_timeout())

            # Main message loop
            await self.message_loop()

        except (NotFoundException, ForbiddenException) as e:
            logger.warning(f"Access denied for user {self.user_id} to chat {self.chat_id}: {e}")
            await self.websocket.close(code=1008, reason=str(e))

        except Exception as e:
            logger.error(f"Error in ChatWebSocketHandler: {e}", exc_info=True)
            await self.send_error("Internal server error")

        finally:
            await self.cleanup_session()
            if self.chat_id:
                await self.connection_manager.disconnect(self.websocket, self.chat_id)

    async def handle_message(self, data: dict):
        """Handle message with activity tracking."""
        self.last_activity = datetime.now()
        await super().handle_message(data)

    async def check_idle_timeout(self):
        """Background task to check for idle timeout and close connection if exceeded."""
        try:
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds

                idle_time = (datetime.now() - self.last_activity).total_seconds()

                if idle_time > settings.websocket_idle_timeout:
                    logger.info(
                        f"Closing WebSocket for chat {self.chat_id} due to idle timeout "
                        f"({idle_time:.0f}s > {settings.websocket_idle_timeout}s)"
                    )
                    await self.websocket.close(code=1000, reason="Idle timeout")
                    break

        except asyncio.CancelledError:
            logger.debug(f"Idle timeout checker cancelled for chat {self.chat_id}")
        except Exception as e:
            logger.error(f"Error in idle timeout checker: {e}", exc_info=True)
