"""Integration tests for UserRepository."""

import pytest
from src.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestUserRepository:
    """Test UserRepository database operations."""

    async def test_create_user(self, test_db_session):
        """Test creating a new user."""
        repo = UserRepository(test_db_session)
        
        # Create user
        user = await repo.create(name="John Doe", email="john@example.com")
        await test_db_session.commit()
        
        # Verify
        assert user.id is not None
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_get_by_id(self, test_db_session):
        """Test getting user by ID."""
        repo = UserRepository(test_db_session)
        
        # Create user
        created_user = await repo.create(name="Jane Doe", email="jane@example.com")
        await test_db_session.commit()
        
        # Get by ID
        found_user = await repo.get_by_id(created_user.id)
        
        # Verify
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.name == "Jane Doe"
        assert found_user.email == "jane@example.com"

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
        repo = UserRepository(test_db_session)
        
        # Create user
        await repo.create(name="Bob Smith", email="bob@example.com")
        await test_db_session.commit()
        
        # Get by email
        found_user = await repo.get_by_email("bob@example.com")
        
        # Verify
        assert found_user is not None
        assert found_user.name == "Bob Smith"
        assert found_user.email == "bob@example.com"

    async def test_get_by_email_not_found(self, test_db_session):
        """Test getting user by non-existent email returns None."""
        repo = UserRepository(test_db_session)
        
        # Try to get non-existent email
        user = await repo.get_by_email("nonexistent@example.com")
        
        # Verify
        assert user is None

    async def test_update_name(self, test_db_session):
        """Test updating user name."""
        repo = UserRepository(test_db_session)
        
        # Create user
        user = await repo.create(name="Old Name", email="user@example.com")
        await test_db_session.commit()
        
        # Update name
        updated_user = await repo.update_name(user, "New Name")
        await test_db_session.commit()
        await test_db_session.refresh(updated_user)
        
        # Verify
        assert updated_user.name == "New Name"
        assert updated_user.email == "user@example.com"

    async def test_delete_user(self, test_db_session):
        """Test deleting user."""
        repo = UserRepository(test_db_session)
        
        # Create user
        user = await repo.create(name="To Delete", email="delete@example.com")
        await test_db_session.commit()
        user_id = user.id
        
        # Delete user
        await repo.delete(user)
        await test_db_session.commit()
        
        # Verify user is deleted
        deleted_user = await repo.get_by_id(user_id)
        assert deleted_user is None
