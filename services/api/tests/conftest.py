import asyncio
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

from shared.database import Base, get_db  # noqa: E402

_test_engine = None
_TestSession = None


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    global _test_engine, _TestSession
    _test_engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    _TestSession = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()
    _test_engine = None
    _TestSession = None


@pytest_asyncio.fixture
async def db_session():
    async with _TestSession() as session:
        yield session


async def _get_test_db():
    async with _TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    from main import app

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client):
    await client.post("/api/auth/register", json={
        "display_name": "Test Owner",
        "email": "test@example.com",
        "password": "test123",
        "role": "owner",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "test123",
    })
    data = resp.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def team_admin_headers(client, db_session):
    from auth.models import UserCreate
    from auth.service import AuthService

    service = AuthService(db_session)
    user = await service.create_user(
        UserCreate(
            display_name="Team Admin",
            email="team-admin@example.com",
            password="test123",
            role="owner",
            global_role="team_admin",
        ),
        requester_global_role="team_admin",
    )
    resp = await client.post("/api/auth/login", json={
        "email": "team-admin@example.com",
        "password": "test123",
    })
    data = resp.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}
