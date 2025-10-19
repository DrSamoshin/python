"""Shared fixtures for API unit tests."""

import pytest
from unittest.mock import AsyncMock

from src.api.services.chat_session_service import ChatSessionService


@pytest.fixture
def chat_service(mock_db_session, mock_redis):
    """Create ChatSessionService instance with mocked dependencies."""
    service = ChatSessionService(mock_db_session, mock_redis)

    # Mock the services
    service.message_service = AsyncMock()
    service.agent_orchestrator = AsyncMock()

    return service