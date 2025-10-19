"""
    Pytest fixtures for testing.
    conftest.py is automatically loaded by pytest.
"""

import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from src.api.core.database import get_db
from src.api.app import create_app
from src.api.core.database import Base
from src.models.user import User  # noqa: F401 - needed for metadata
from redis.asyncio import Redis
from src.api.core.redis_client import get_redis
from src.models import Chat, Message  # noqa: F401 - needed for metadata

# Test database URL (docker-compose.test.yml uses port 5433)
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5433/myapp_test"


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(test_db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with test database session override."""
    app = create_app()

    # Override get_db to use test_db_session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Create user and return auth headers."""
    response = await client.post(
        "/v1/users",
        json={"apple_id": "test_apple_id"}
    )
    data = response.json()
    access_token = data["data"]["tokens"]["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="function")
async def test_redis():
    """Create test Redis client."""
    # Connect to test Redis (port 6380 from docker-compose.test.yml)
    redis = Redis.from_url(
        "redis://localhost:6380/0",
        decode_responses=True
    )

    yield redis

    # Cleanup: flush test database
    await redis.flushdb()
    await redis.aclose()


@pytest_asyncio.fixture(scope="function")
async def client_with_redis(test_db_session, test_redis) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with test database and Redis override."""
    app = create_app()

    # Override get_db to use test_db_session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db_session

    # Override get_redis to use test_redis
    async def override_get_redis() -> Redis:
        return test_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_chat(test_db_session: AsyncSession, auth_headers: dict) -> Chat:
    """Create a test chat."""
    from src.repositories.chat_repository import ChatRepository

    # Extract user_id from token
    token = auth_headers["Authorization"].replace("Bearer ", "")
    from src.api.services.auth_service import AuthService
    auth_service = AuthService()
    user_id = auth_service.verify_token(token, "access")

    # Create chat
    repo = ChatRepository(test_db_session)
    chat = await repo.create(user_id=user_id, title="Test Chat")
    await test_db_session.commit()

    return chat
