"""Integration tests for Users API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestUsersAPI:
    """Test Users CRUD API endpoints."""

    async def test_create_user(self, client: AsyncClient):
        name = "John Doe"
        email = "john@example.com"
        apple_id = "apple_id"
        """Test POST /users - create new user."""
        response = await client.post(
            "/v1/users",
            json={"name": name, "email": email, "apple_id": apple_id}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == name
        assert data["data"]["email"] == email
        assert data["data"]["apple_id"] == apple_id
        assert "id" in data["data"]
        assert "created_at" in data["data"]

    async def test_create_user_only_with_apple_id(self, client: AsyncClient):
        apple_id = "apple_id"
        """Test POST /users - create new user."""
        response = await client.post(
            "/v1/users",
            json={"apple_id": apple_id}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] is None
        assert data["data"]["email"] is None
        assert data["data"]["apple_id"] == apple_id
        assert "id" in data["data"]
        assert "created_at" in data["data"]

    async def test_create_user_duplicate_apple_id(self, client: AsyncClient):
        """Test POST /users - duplicate apple_id returns 200."""
        apple_id = "apple_id"
        # Create first user
        first_user = await client.post(
            "/v1/users",
            json={"apple_id": apple_id}
        )
        
        # Try to create second user with same email
        response = await client.post(
            "/v1/users",
            json={"apple_id": apple_id}
        )
        
        # Verify error
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == first_user.json()["data"]["id"]

    async def test_get_user(self, client: AsyncClient):
        """Test GET /users/{id} - get user by ID."""
        apple_id = "apple_id"
        # Create user
        create_response = await client.post(
            "/v1/users",
            json={"apple_id": apple_id}
        )
        user_id = create_response.json()["data"]["id"]
        
        # Get user
        response = await client.get(f"/v1/users/{user_id}")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == user_id
        assert data["data"]["apple_id"] == apple_id

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
        name = "John Doe"
        new_name = "John"
        email = "john@example.com"
        apple_id = "apple_id"
        # Create user
        create_response = await client.post(
            "/v1/users",
            json={"apple_id": apple_id, "name": name, "email": email}
        )
        user_id = create_response.json()["data"]["id"]
        
        # Update name
        response = await client.patch(
            f"/v1/users/{user_id}",
            json={"name": new_name}
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["apple_id"] == apple_id
        assert data["data"]["name"] == new_name
        assert data["data"]["email"] == email

    async def test_delete_user(self, client: AsyncClient):
        """Test DELETE /users/{id} - delete user."""
        name = "John Doe"
        email = "john@example.com"
        apple_id = "apple_id"
        # Create user
        create_response = await client.post(
            "/v1/users",
            json={"apple_id": apple_id, "name": name, "email": email}
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
