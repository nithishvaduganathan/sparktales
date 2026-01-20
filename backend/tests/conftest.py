"""Test configuration and fixtures."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
# Import all models to ensure they're registered with Base.metadata
from app.models import User, Document, Group, GroupMember, Message, AuditLog, AIQuery


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_sparktales.db"


# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)


# Create test session factory
test_async_session = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """Override database dependency for testing."""
    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """Set up test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(setup_database):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database):
    """Create database session for testing."""
    async with test_async_session() as session:
        yield session
