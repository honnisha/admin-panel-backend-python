import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class ModelBase(DeclarativeBase):
    pass


@pytest.fixture
async def sqlite_sessionmaker():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
    )

    # Enable FK checks in SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)

    SessionMaker = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    yield SessionMaker

    await engine.dispose()
