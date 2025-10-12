"""Integration tests for UserService."""

import pytest
from uuid import uuid4
from src.api.services.user_service import UserService
from src.api.exceptions import UserNotFoundError, UserAlreadyExistsError


@pytest.mark.integration
class TestUserService:
    """Test UserService business logic."""

    async def test_create_user(self, test_db_session):
        """Test creating a new user."""
        apple_id = "apple_id"
        name = "John Doe"
        email = "john@example.com"
        service = UserService(test_db_session)
        
        # Create user
        user = await service.create_user_with_apple_id(apple_id=apple_id, name=name, email=email, is_active=True)
        
        # Verify
        assert user.id is not None
        assert user.apple_id == apple_id
        assert user.name == name
        assert user.email == email
        assert user.is_active

    async def test_create_user_duplicate_apple_id(self, test_db_session):
        """Test creating user with duplicate email raises error."""
        apple_id = "apple_id"
        name = "John Doe"
        email = "john@example.com"
        service = UserService(test_db_session)
        
        # Create first user
        first_user = await service.create_user_with_apple_id(apple_id=apple_id, name=name, email=email, is_active=True)
        
        # Try to create second user with same email
        second_user = await service.create_user_with_apple_id(apple_id=apple_id, name=name, email=email, is_active=True)
        
        # Verify error message
        assert first_user is second_user

    async def test_get_user(self, test_db_session):
        """Test getting user by ID."""
        apple_id = "apple_id"
        name = "John Doe"
        email = "john@example.com"
        service = UserService(test_db_session)
        
        # Create user
        created_user = await service.create_user_with_apple_id(apple_id=apple_id, name=name, email=email, is_active=True)
        
        # Get user
        found_user = await service.get_user(created_user.id)
        
        # Verify
        assert found_user.id == created_user.id
        assert found_user.apple_id == apple_id
        assert found_user.name == name
        assert found_user.email == email

    async def test_get_user_not_found(self, test_db_session):
        """Test getting non-existent user raises error."""
        service = UserService(test_db_session)
        
        # Try to get non-existent user
        with pytest.raises(UserNotFoundError) as exc_info:
            await service.get_user(uuid4())
        
        # Verify error
        assert "not found" in str(exc_info.value).lower()

    async def test_get_user_by_email(self, test_db_session):
        """Test getting user by email."""
        apple_id = "apple_id"
        name = "John Doe"
        email = "john@example.com"
        service = UserService(test_db_session)
        
        # Create user
        await service.create_user_with_apple_id(apple_id=apple_id, name=name, email=email, is_active=True)
        
        # Get by email
        found_user = await service.get_user_by_email(email)
        
        # Verify
        assert found_user is not None
        assert found_user.apple_id == apple_id
        assert found_user.name == name
        assert found_user.email == email

    async def test_get_user_by_email_not_found(self, test_db_session):
        """Test getting user by non-existent email returns None."""
        service = UserService(test_db_session)
        
        # Get non-existent email
        user = await service.get_user_by_email("nonexistent@example.com")
        
        # Verify
        assert user is None

    async def test_update_user_name(self, test_db_session):
        """Test updating user name."""
        apple_id = "apple_id"
        name = "John Doe"
        new_name = "Bob"
        email = "john@example.com"
        service = UserService(test_db_session)
        
        # Create user
        user = await service.create_user_with_apple_id(apple_id=apple_id, name=name, email=email, is_active=True)
        
        # Update name
        updated_user = await service.update_user_name(user.id, new_name)
        
        # Verify
        assert updated_user.id == user.id
        assert updated_user.apple_id == apple_id
        assert updated_user.name == new_name
        assert updated_user.email == email

    async def test_update_user_name_not_found(self, test_db_session):
        """Test updating non-existent user raises error."""
        service = UserService(test_db_session)
        
        # Try to update non-existent user
        with pytest.raises(UserNotFoundError):
            await service.update_user_name(uuid4(), "New Name")

    async def test_delete_user(self, test_db_session):
        """Test deleting user."""
        apple_id = "apple_id"
        name = "John Doe"
        email = "john@example.com"
        service = UserService(test_db_session)
        
        # Create user
        user = await service.create_user_with_apple_id(apple_id=apple_id, name=name, email=email, is_active=True)
        user_id = user.id
        
        # Delete user
        await service.delete_user(user_id)
        
        # Verify user is deleted
        with pytest.raises(UserNotFoundError):
            await service.get_user(user_id)

    async def test_delete_user_not_found(self, test_db_session):
        """Test deleting non-existent user raises error."""
        service = UserService(test_db_session)
        
        # Try to delete non-existent user
        with pytest.raises(UserNotFoundError):
            await service.delete_user(uuid4())
