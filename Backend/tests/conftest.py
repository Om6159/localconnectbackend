import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geography
import geoalchemy2.admin
import geoalchemy2.admin.dialects.sqlite
from httpx import AsyncClient, ASGITransport

from app.core.database import Base, get_db
from app.main import app

# Disable GeoAlchemy2 Spatialite DDL triggers for SQLite unit tests
geoalchemy2.admin.after_create = lambda *args, **kwargs: None
geoalchemy2.admin.before_drop = lambda *args, **kwargs: None
geoalchemy2.admin.dialects.sqlite.create_spatial_index = lambda *args, **kwargs: None

# Render PostgreSQL-specific types on SQLite for unit testing
@compiles(Geography, "sqlite")
def compile_geography_sqlite(type_, compiler, **kw):
    return "VARCHAR"

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

# Register mock PostGIS SQLite functions on DBAPI connection
@event.listens_for(test_engine.sync_engine, "connect")
def register_mock_postgis_functions(dbapi_conn, record):
    dbapi_conn.create_function("ST_GeogFromText", 1, lambda val: val)
    dbapi_conn.create_function("ST_GeomFromText", 1, lambda val: val)
    dbapi_conn.create_function("ST_WKTToSQL", 1, lambda val: val)
    dbapi_conn.create_function("CreateSpatialIndex", 2, lambda a, b: 1)
    dbapi_conn.create_function("ST_DWithin", 3, lambda a, b, c: 1)
    dbapi_conn.create_function("ST_Distance", 2, lambda a, b: 0.0)
    dbapi_conn.create_function("AsBinary", 1, lambda val: None)


TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture providing a fresh in-memory database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Fixture providing an async HTTP client connected to the FastAPI app with DB override."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()
