import pytest

from example.sqlite import ASYNC_ENGINE, async_sessionmaker_, recreate_tables_async


@pytest.fixture
async def sqlite_sessionmaker():
    await recreate_tables_async()
    try:
        yield async_sessionmaker_
    finally:
        await ASYNC_ENGINE.dispose()
