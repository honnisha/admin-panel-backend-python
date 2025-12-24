import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class ModelBase(DeclarativeBase):
    pass


@pytest.fixture
async def sqlite_sessionmaker():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)

    SessionMaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    yield SessionMaker

    await engine.dispose()
