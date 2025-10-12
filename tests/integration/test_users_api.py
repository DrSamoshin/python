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
        assert data["data"]["user"]["name"] == name
        assert data["data"]["user"]["email"] == email
        assert data["data"]["user"]["apple_id"] == apple_id
        assert "id" in data["data"]["user"]
        assert "created_at" in data["data"]["user"]

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
        assert data["data"]["user"]["name"] is None
        assert data["data"]["user"]["email"] is None
        assert data["data"]["user"]["apple_id"] == apple_id
        assert "id" in data["data"]["user"]
        assert "created_at" in data["data"]["user"]

    async def test_create_user_duplicate_apple_id(self, client: AsyncClient):
        """Test POST /users - duplicate apple_id returns 200."""
        apple_id = "apple_id"
        # Create first user
        first_user = await client.post(
            "/v1/users",
            json={"apple_id": apple_id}
        )
        
        # Try to create second user with same email
        second_user = await client.post(
            "/v1/users",
            json={"apple_id": apple_id}
        )
        
        # Verify error
        assert second_user.status_code == 200
        first_user_data = first_user.json()
        second_user_data = second_user.json()
        assert first_user_data == second_user_data

    async def test_get_user(self, client: AsyncClient):
        """Test GET /users/{id} - get user by ID."""
        apple_id = "apple_id"
        # Create user
        create_response = await client.post(
            "/v1/users",
            json={"apple_id": apple_id}
        )
        user_id = create_response.json()["data"]["user"]["id"]
        # Add headers в client
        client.headers.update({
            "Authorization": f"Bearer {create_response.json()['data']['tokens']['access_token']}"
        })

        # Get user
        response = await client.get(f"/v1/users")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == user_id
        assert data["data"]["apple_id"] == apple_id

    async def test_get_user_without_token(self, client: AsyncClient):
        """Test GET /users/{id} - get user by ID."""
        apple_id = "apple_id"
        # Create user
        create_response = await client.post(
            "/v1/users",
            json={"apple_id": apple_id}
        )
        user_id = create_response.json()["data"]["user"]["id"]

        # Get user
        response = await client.get(f"/v1/users")

        # Verify 401 error
        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "UNAUTHORIZED"

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
        user_id = create_response.json()["data"]["user"]["id"]
        # Add headers в client
        client.headers.update({
            "Authorization": f"Bearer {create_response.json()['data']['tokens']['access_token']}"
        })

        # Update name
        response = await client.patch(
            f"/v1/users",
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
        user_id = create_response.json()["data"]["user"]["id"]
        client.headers.update({
            "Authorization": f"Bearer {create_response.json()['data']['tokens']['access_token']}"
        })
        
        # Delete user
        response = await client.delete(f"/v1/users")
        
        # Verify
        assert response.status_code == 204
        assert response.content == b""
        
        # Verify user is deleted
        get_response = await client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 404

    async def test_refresh_token(self, client: AsyncClient):
        """Test POST /users/refresh - refresh access token."""
        apple_id = "apple_id"

        # Create user and get tokens
        create_response = await client.post(
            "/v1/users",
            json={"apple_id": apple_id}
        )

        assert create_response.status_code == 200
        tokens = create_response.json()["data"]["tokens"]
        old_access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Refresh tokens
        refresh_response = await client.post(
            "/v1/users/refresh",
            json={"refresh_token": refresh_token}
        )

        # Verify response
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert data["status"] == "success"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

        # Verify new tokens are different from old ones
        new_access_token = data["data"]["access_token"]

        # Verify new access token works
        client.headers.update({
            "Authorization": f"Bearer {new_access_token}"
        })
        user_response = await client.get("/v1/users")
        assert user_response.status_code == 200
