"""Shared fixtures for agent unit tests."""

import pytest
from unittest.mock import patch

from src.agent.orchestrator import AgentOrchestrator
from src.agent.llm.openai_client import OpenAIClient
from src.agent.dto import AgentMessage, AgentRequest


@pytest.fixture
def openai_client():
    """Create OpenAIClient instance for testing."""
    with patch('src.agent.llm.openai_client.settings') as mock_settings:
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o-mini"
        mock_settings.openai_temperature = 0.7
        mock_settings.openai_max_tokens = 2000

        client = OpenAIClient()
        return client


@pytest.fixture
def sample_messages():
    """Sample AgentMessage list for testing."""
    return [
        AgentMessage(role="user", content="Hello"),
        AgentMessage(role="assistant", content="Hi there!"),
        AgentMessage(role="user", content="How are you?")
    ]


@pytest.fixture
def orchestrator():
    """Create AgentOrchestrator instance for testing."""
    return AgentOrchestrator()


@pytest.fixture
def sample_request():
    """Sample AgentRequest for testing."""
    from uuid import UUID
    return AgentRequest(
        chat_history=[
            AgentMessage(role="user", content="Hello"),
            AgentMessage(role="assistant", content="Hi there!"),
        ],
        user_message=AgentMessage(role="user", content="How are you?"),
        chat_id=UUID("00000000-0000-0000-0000-000000000001")
    )