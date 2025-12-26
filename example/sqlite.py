from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ASYNC_ENGINE = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    future=True,
)


@event.listens_for(ASYNC_ENGINE.sync_engine, "connect")
def _enable_fk_async(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async_sessionmaker_ = async_sessionmaker(
    ASYNC_ENGINE,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def recreate_tables_async():
    from example.sections.models import ModelBase

    async with ASYNC_ENGINE.begin() as conn:
        await conn.run_sync(ModelBase.metadata.drop_all)
        await conn.run_sync(ModelBase.metadata.create_all)


@asynccontextmanager
async def lifespan(app):
    await recreate_tables_async()

    from example.sections import models

    await models.CurrencyFactory.create_batch_async(5)
    await models.MerchantFactory.create_batch_async(10)
    await models.TerminalFactory.create_batch_async(15)

    yield
