"""Demo WebSocket handler for temporary users."""

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from uuid import uuid4
import logging
import asyncio
from datetime import datetime

from src.api.v1.websocket.base_handler import BaseWebSocketHandler
from src.api.v1.websocket.connection_manager import ConnectionManager
from src.api.services import ChatService, UserService
from src.api.core.configs import settings
from src.api.exceptions import NotFoundException, ForbiddenException

logger = logging.getLogger(__name__)


class DemoWebSocketHandler(BaseWebSocketHandler):
    """Handler for demo chat WebSocket connections with temporary users."""

    def __init__(
            self,
            websocket: WebSocket,
            session: AsyncSession,
            redis: Redis,
            connection_manager: ConnectionManager
    ):
        super().__init__(websocket, session, redis, connection_manager)
        self.user_service = UserService(session)
        self.chat_service = ChatService(session)

        # Lifetime tracking
        self.connection_start_time = datetime.now()
        self.lifetime_check_task = None

    async def setup_session(self):
        """Create temporary demo user and chat."""
        # Generate unique demo apple_id
        demo_apple_id = f"demo_{uuid4()}"

        # Create demo user
        user = await self.user_service.create_user_with_apple_id(
            apple_id=demo_apple_id,
            name=f"Demo User",
            email=None,
            is_active=True
        )
        self.user_id = user.id
        logger.info(f"Created demo user: {self.user_id} ({demo_apple_id})")

        # Create chat for demo user
        chat = await self.chat_service.create_chat(
            user_id=self.user_id,
            title="Demo Chat"
        )
        self.chat_id = chat.id
        logger.info(f"Created demo chat: {self.chat_id}")

    async def cleanup_session(self):
        """Cancel lifetime checker and delete demo user."""
        # Cancel lifetime checker
        if self.lifetime_check_task:
            self.lifetime_check_task.cancel()
            try:
                await self.lifetime_check_task
            except asyncio.CancelledError:
                pass

        # Delete demo user and all associated data (cascade)
        if self.user_id:
            try:
                await self.user_service.delete_user(self.user_id)
                logger.info(f"Deleted demo user and all data: {self.user_id}")
            except Exception as e:
                logger.error(f"Error deleting demo user {self.user_id}: {e}", exc_info=True)

    async def handle_connection(self):
        """Extended connection handler with 2-minute lifetime limit."""
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
            logger.info(f"Demo session started: user={self.user_id}, chat={self.chat_id}, messages={len(history)}")

            # Start lifetime checker (2 minutes max)
            self.lifetime_check_task = asyncio.create_task(self.check_lifetime())

            # Main message loop
            await self.message_loop()

        except (NotFoundException, ForbiddenException) as e:
            logger.warning(f"Access denied for demo chat {self.chat_id}: {e}")
            await self.websocket.close(code=1008, reason=str(e))

        except Exception as e:
            logger.error(f"Error in DemoWebSocketHandler: {e}", exc_info=True)
            await self.send_error("Internal server error")

        finally:
            await self.cleanup_session()
            if self.chat_id:
                await self.connection_manager.disconnect(self.websocket, self.chat_id)

    async def check_lifetime(self):
        """Background task to check connection lifetime and close after 2 minutes."""
        try:
            while True:
                await asyncio.sleep(10)  # Check every 10 seconds

                elapsed_time = (datetime.now() - self.connection_start_time).total_seconds()

                if elapsed_time >= settings.demo_ws_lifetime:
                    logger.info(
                        f"Closing demo WebSocket for chat {self.chat_id} - lifetime expired "
                        f"({elapsed_time:.0f}s >= {settings.demo_ws_lifetime}s)"
                    )
                    await self.websocket.close(code=1000, reason="Demo session expired (2 minutes)")
                    break

        except asyncio.CancelledError:
            logger.debug(f"Lifetime checker cancelled for demo chat {self.chat_id}")
        except Exception as e:
            logger.error(f"Error in lifetime checker: {e}", exc_info=True)