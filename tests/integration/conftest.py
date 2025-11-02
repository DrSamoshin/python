import asyncio
from datetime import datetime
import os
import aiosqlite
from dotenv import load_dotenv
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import AsyncGenerator


load_dotenv()
BASE_URL = os.getenv("API_URL", "")

@pytest_asyncio.fixture(scope='function')
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        base_url=BASE_URL
    ) as client:
        yield client

@pytest_asyncio.fixture(scope='function')
async def get_auth_header(client: AsyncClient) -> dict:
    response = await client.post(url="/v1/users", json={"apple_id": "test_apple_id"})
    data = response.json()
    access_token = data["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

    # token = base64.b64encode(f"{username}:{password}".encode()).decode()
    # return {"Authorization": f"Basic {token}"}

@pytest.fixture(scope="function")
async def db():
    conn = await aiosqlite.connect(":memory:") # создаём асинхронную SQLite БД в памяти
    await conn.execute("""
        CREATE TABLE responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT,
            method TEXT,
            response_code INTEGER,
            response_body TEXT
        )
    """)
    await conn.commit()
    yield conn
    await conn.close()

# ---------------------------------------------------------------------------------------------------------------------
async def init_db():
    conn = await aiosqlite.connect("test_results.db")
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT,
            status TEXT,
            duration REAL,
            timestamp TEXT
        )
    """)
    await conn.commit()
    return conn

def pytest_runtest_logreport(report):
    if report.when == "call":  # только после выполнения теста
        status = "PASSED" if report.passed else "FAILED"
        duration = round(report.duration, 3)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        async def log_to_db():
            conn = await init_db()
            await conn.execute(
                "INSERT INTO test_results (test_name, status, duration, timestamp) VALUES (?, ?, ?, ?)",
                (report.nodeid, status, duration, timestamp)
            )
            await conn.commit()
            await conn.close()

        asyncio.run(log_to_db())

def pytest_sessionfinish(session, exitstatus):
    print("\n=== DB Report ===")

    async def show_results():
        conn = await aiosqlite.connect("test_results.db")
        async with conn.execute("SELECT test_name, status, duration, timestamp FROM test_results") as cursor:
            async for name, status, dur, ts in cursor:
                print(f"{status:6} | {dur:>5}s | {name} | {ts}")
        await conn.close()

    asyncio.run(show_results())
