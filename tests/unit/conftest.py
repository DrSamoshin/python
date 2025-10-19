"""Shared fixtures for unit tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from src.models import MessageRole


@pytest.fixture
def mock_db_session():
    """Mock AsyncSession for database operations."""
    return MagicMock()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return MagicMock()


@pytest.fixture
def sample_chat_id():
    """Sample chat UUID."""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user UUID."""
    return uuid4()


@pytest.fixture
def mock_user_message():
    """Mock user message."""
    msg = MagicMock()
    msg.role = MessageRole.USER
    msg.content = "Hello"
    return msg


@pytest.fixture
def mock_assistant_message():
    """Mock assistant message."""
    msg = MagicMock()
    msg.role = MessageRole.ASSISTANT
    msg.content = "Hi there!"
    return msg