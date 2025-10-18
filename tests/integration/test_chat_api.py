"""Integration tests for Chats REST API."""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
class TestChatsAPI:
    """Test Chats REST API endpoints."""

    async def test_create_chat(self, client_with_redis: AsyncClient, auth_headers: dict):
        """Test creating a new chat."""
        response = await client_with_redis.post(
            "/v1/chats",
            json={"title": "My New Chat"},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My New Chat"
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data

    async def test_create_chat_without_title(self, client_with_redis: AsyncClient, auth_headers:
    dict):
        """Test creating chat without title."""
        response = await client_with_redis.post(
            "/v1/chats",
            json={},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] is None

    async def test_create_chat_unauthorized(self, client_with_redis: AsyncClient):
        """Test creating chat without authentication."""
        response = await client_with_redis.post(
            "/v1/chats",
            json={"title": "Test"}
        )

        assert response.status_code == 401

    async def test_get_user_chats(self, client_with_redis: AsyncClient, auth_headers: dict,
                                  test_chat):
        """Test getting user's chats."""
        response = await client_with_redis.get(
            "/v1/chats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == str(test_chat.id)

    async def test_get_user_chats_pagination(self, client_with_redis: AsyncClient, auth_headers:
    dict):
        """Test pagination for user chats."""
        # Create multiple chats
        for i in range(5):
            await client_with_redis.post(
                "/v1/chats",
                json={"title": f"Chat {i}"},
                headers=auth_headers
            )

        # Test limit
        response = await client_with_redis.get(
            "/v1/chats?limit=3",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Test offset
        response = await client_with_redis.get(
            "/v1/chats?limit=3&offset=3",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Only 2 remaining

    async def test_get_chat_by_id(self, client_with_redis: AsyncClient, auth_headers: dict,
                                  test_chat):
        """Test getting specific chat by ID."""
        response = await client_with_redis.get(
            f"/v1/chats/{test_chat.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_chat.id)
        assert data["title"] == test_chat.title

    async def test_get_chat_not_found(self, client_with_redis: AsyncClient, auth_headers: dict):
        """Test getting non-existent chat."""
        fake_id = uuid4()
        response = await client_with_redis.get(
            f"/v1/chats/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_chat_forbidden(self, client: AsyncClient, test_chat):
        """Test getting chat that belongs to another user."""
        # Create different user
        response = await client.post(
            "/v1/users",
            json={"apple_id": "another_user"}
        )
        other_user_token = response.json()["data"]["tokens"]["access_token"]
        other_headers = {"Authorization": f"Bearer {other_user_token}"}

        # Try to access first user's chat
        response = await client.get(
            f"/v1/chats/{test_chat.id}",
            headers=other_headers
        )

        assert response.status_code == 403

    async def test_update_chat_title(self, client_with_redis: AsyncClient, auth_headers: dict,
                                     test_chat):
        """Test updating chat title."""
        response = await client_with_redis.patch(
            f"/v1/chats/{test_chat.id}",
            json={"title": "Updated Title"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["id"] == str(test_chat.id)

    async def test_delete_chat(self, client_with_redis: AsyncClient, auth_headers: dict,
                               test_chat):
        """Test deleting a chat."""
        response = await client_with_redis.delete(
            f"/v1/chats/{test_chat.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["message"] == "Chat deleted successfully"

        # Verify chat is deleted
        response = await client_with_redis.get(
            f"/v1/chats/{test_chat.id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_get_chat_messages_empty(self, client_with_redis: AsyncClient, auth_headers:
    dict, test_chat):
        """Test getting messages from empty chat."""
        response = await client_with_redis.get(
            f"/v1/chats/{test_chat.id}/messages",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_get_chat_messages_with_data(
            self,
            client_with_redis: AsyncClient,
            auth_headers: dict,
            test_chat,
            test_db_session
    ):
        """Test getting messages from chat with messages."""
        from src.repositories.message_repository import MessageRepository
        from src.models import MessageRole

        # Create some messages
        repo = MessageRepository(test_db_session)
        await repo.create(test_chat.id, MessageRole.USER, "Hello")
        await repo.create(test_chat.id, MessageRole.ASSISTANT, "Hi there")
        await test_db_session.commit()

        response = await client_with_redis.get(
            f"/v1/chats/{test_chat.id}/messages",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["content"] == "Hello"
        assert data[1]["content"] == "Hi there"
