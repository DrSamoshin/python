"""Integration tests for Users API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestUsersAPI:
    """Test Users CRUD API endpoints."""

    async def test_create_user(self, client: AsyncClient):
        """Test POST /users - create new user."""
        response = await client.post(
            "/v1/users",
            json={"name": "John Doe", "email": "john@example.com"}
        )
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "John Doe"
        assert data["data"]["email"] == "john@example.com"
        assert "id" in data["data"]
        assert "created_at" in data["data"]

    async def test_create_user_duplicate_email(self, client: AsyncClient):
        """Test POST /users - duplicate email returns 400."""
        # Create first user
        await client.post(
            "/v1/users",
            json={"name": "John Doe", "email": "john@example.com"}
        )
        
        # Try to create second user with same email
        response = await client.post(
            "/v1/users",
            json={"name": "Jane Doe", "email": "john@example.com"}
        )
        
        # Verify error
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "USER_ALREADY_EXISTS"
        assert "john@example.com" in data["error"]["message"]

    async def test_get_user(self, client: AsyncClient):
        """Test GET /users/{id} - get user by ID."""
        # Create user
        create_response = await client.post(
            "/v1/users",
            json={"name": "Jane Doe", "email": "jane@example.com"}
        )
        user_id = create_response.json()["data"]["id"]
        
        # Get user
        response = await client.get(f"/v1/users/{user_id}")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == user_id
        assert data["data"]["name"] == "Jane Doe"
        assert data["data"]["email"] == "jane@example.com"

    async def test_get_user_not_found(self, client: AsyncClient):
        """Test GET /users/{id} - non-existent user returns 404."""
        from uuid import uuid4
        
        response = await client.get(f"/v1/users/{uuid4()}")
        
        # Verify error
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "USER_NOT_FOUND"

    async def test_update_user_name(self, client: AsyncClient):
        """Test PATCH /users/{id} - update user name."""
        # Create user
        create_response = await client.post(
            "/v1/users",
            json={"name": "Old Name", "email": "user@example.com"}
        )
        user_id = create_response.json()["data"]["id"]
        
        # Update name
        response = await client.patch(
            f"/v1/users/{user_id}",
            json={"name": "New Name"}
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "New Name"
        assert data["data"]["email"] == "user@example.com"

    async def test_delete_user(self, client: AsyncClient):
        """Test DELETE /users/{id} - delete user."""
        # Create user
        create_response = await client.post(
            "/v1/users",
            json={"name": "To Delete", "email": "delete@example.com"}
        )
        user_id = create_response.json()["data"]["id"]
        
        # Delete user
        response = await client.delete(f"/v1/users/{user_id}")
        
        # Verify
        assert response.status_code == 204
        assert response.content == b""
        
        # Verify user is deleted
        get_response = await client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 404

    async def test_delete_user_not_found(self, client: AsyncClient):
        """Test DELETE /users/{id} - non-existent user returns 404."""
        from uuid import uuid4
        
        response = await client.delete(f"/v1/users/{uuid4()}")
        
        # Verify error
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "USER_NOT_FOUND"
