
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models import Episode


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:

    # Create isolated in-memory test database
    engine = create_async_engine(TEST_DATABASE_URL)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Override the production database dependency
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Create HTTP test client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client

    # Cleanup
    app.dependency_overrides.clear()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await engine.dispose()


async def test_episode_crud(client: AsyncClient):

    # 1. CREATE
    response = await client.post(
        "/api/v1/episodes",
        json={
            "title": "Test Episode",
            "description": "Testing automated API"
        }
    )

    assert response.status_code == 201

    created_episode = response.json()
    episode_id = created_episode["id"]

    assert created_episode["title"] == "Test Episode"
    assert created_episode["status"] == "draft"

    # 2. GET ALL
    response = await client.get("/api/v1/episodes")

    assert response.status_code == 200
    assert len(response.json()) == 1

    # 3. GET BY ID
    response = await client.get(
        f"/api/v1/episodes/{episode_id}"
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Test Episode"

    # 4. UPDATE
    response = await client.put(
        f"/api/v1/episodes/{episode_id}",
        json={
            "title": "Updated Test Episode"
        }
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Test Episode"

    # Description should remain unchanged
    assert response.json()["description"] == "Testing automated API"

    # 5. DELETE
    response = await client.delete(
        f"/api/v1/episodes/{episode_id}"
    )

    assert response.status_code == 204

    # 6. VERIFY DELETION
    response = await client.get(
        f"/api/v1/episodes/{episode_id}"
    )

    assert response.status_code == 404


async def test_create_episode_validation(client: AsyncClient):

    response = await client.post(
        "/api/v1/episodes",
        json={
            "title": "",
            "description": "Invalid episode"
        }
    )

    assert response.status_code == 422
