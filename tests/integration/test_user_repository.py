"""Integration tests for UserRepository."""

import pytest
from src.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestUserRepository:
    """Test UserRepository database operations."""

    async def test_create_user(self, test_db_session):
        """Test creating a new user."""
        apple_id = "apple_id"
        name = "John Doe"
        email = "john@example.com"
        repo = UserRepository(test_db_session)
        
        # Create user
        user = await repo.create(apple_id=apple_id, name=name, email=email, is_active=True)
        await test_db_session.commit()
        
        # Verify
        assert user.id is not None
        assert user.apple_id == apple_id
        assert user.name == name
        assert user.email == email
        assert user.is_active
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_create_user_only_with_apple_id(self, test_db_session):
        """Test creating a new user only with apple_id."""
        apple_id = "apple_id"
        repo = UserRepository(test_db_session)

        # Create user
        user = await repo.create(apple_id=apple_id)
        await test_db_session.commit()

        # Verify
        assert user.id is not None
        assert user.apple_id == apple_id
        assert user.name is None
        assert user.email is None
        assert user.is_active
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_get_by_id(self, test_db_session):
        """Test getting user by ID."""
        apple_id = "apple_id"
        name = "John Doe"
        email = "john@example.com"
        repo = UserRepository(test_db_session)
        
        # Create user
        created_user = await repo.create(apple_id=apple_id, name=name, email=email, is_active=True)
        await test_db_session.commit()
        
        # Get by ID
        found_user = await repo.get_by_id(created_user.id)
        
        # Verify
        assert found_user is created_user

    async def test_get_by_id_not_found(self, test_db_session):
        """Test getting non-existent user returns None."""
        repo = UserRepository(test_db_session)
        
        # Try to get non-existent user
        from uuid import uuid4
        user = await repo.get_by_id(uuid4())
        
        # Verify
        assert user is None

    async def test_get_by_email(self, test_db_session):
        """Test getting user by email."""
        apple_id = "apple_id"
        name = "John Doe"
        email = "john@example.com"
        repo = UserRepository(test_db_session)
        
        # Create user
        created_user = await repo.create(apple_id=apple_id, name=name, email=email, is_active=True)
        await test_db_session.commit()
        
        # Get by email
        found_user = await repo.get_by_email(email)
        
        # Verify
        assert found_user is created_user

    async def test_get_by_email_not_found(self, test_db_session):
        """Test getting user by non-existent email returns None."""
        repo = UserRepository(test_db_session)
        
        # Try to get non-existent email
        user = await repo.get_by_email("nonexistent@example.com")
        
        # Verify
        assert user is None

    async def test_update_name(self, test_db_session):
        """Test updating user name."""
        apple_id = "apple_id"
        name = "John Doe"
        new_name = "Bob"
        email = "john@example.com"
        repo = UserRepository(test_db_session)
        
        # Create user
        user = await repo.create(apple_id=apple_id, name=name, email=email, is_active=True)
        await test_db_session.commit()
        
        # Update name
        updated_user = await repo.update_name(user, new_name)
        await test_db_session.commit()
        await test_db_session.refresh(updated_user)
        
        # Verify
        assert updated_user.name == new_name
        assert updated_user.id == user.id
        assert updated_user.apple_id == apple_id

    async def test_delete_user(self, test_db_session):
        """Test deleting user."""
        apple_id = "apple_id"
        name = "John Doe"
        email = "john@example.com"
        repo = UserRepository(test_db_session)
        
        # Create user
        user = await repo.create(apple_id=apple_id, name=name, email=email, is_active=True)
        await test_db_session.commit()
        user_id = user.id
        
        # Delete user
        await repo.delete(user)
        await test_db_session.commit()
        
        # Verify user is deleted
        deleted_user = await repo.get_by_id(user_id)
        assert deleted_user is None
