import pytest

from admin_panel import auth, schema, sqlalchemy
from example.main import CustomLanguageManager
from example.sections.models import CurrencyFactory, MerchantFactory, Terminal, TerminalFactory


@pytest.mark.asyncio
async def test_list_filter(sqlite_sessionmaker):
    category = sqlalchemy.SQLAlchemyAdmin(
        model=Terminal,
        db_async_session=sqlite_sessionmaker,
        table_schema=sqlalchemy.SQLAlchemyFieldsSchema(
            model=Terminal,
            fields=['id'],
        ),
        table_filters=sqlalchemy.SQLAlchemyFieldsSchema(
            model=Terminal,
            fields=['id', 'title'],
        ),
    )
    language_manager = CustomLanguageManager('ru')
    user = auth.UserABC(username="test")

    merchant = await MerchantFactory(title="Test merch")
    currency = await CurrencyFactory()
    terminal_1 = await TerminalFactory(title='Test terminal', merchant=merchant, currency=currency)
    terminal_2 = await TerminalFactory(title='Test terminal second', merchant=merchant, currency=currency)
    await TerminalFactory(title='other', merchant=merchant, currency=currency)

    list_result: dict = await category.get_list(
        list_data=schema.ListData(filters={'id': terminal_1.id}),
        user=user,
        language_manager=language_manager,
    )
    assert list_result == schema.TableListResult(data=[{'id': 1}], total_count=1), 'поиск по id'

    list_result: dict = await category.get_list(
        list_data=schema.ListData(filters={'title': 'Test terminal second'}),
        user=user,
        language_manager=language_manager,
    )
    assert list_result == schema.TableListResult(data=[{'id': terminal_2.id}], total_count=1), 'Полная строка'

    list_result: dict = await category.get_list(
        list_data=schema.ListData(filters={'title': 'Test'}),
        user=user,
        language_manager=language_manager,
    )
    assert list_result == schema.TableListResult(data=[{'id': terminal_1.id}, {'id': terminal_2.id}], total_count=2), 'Частичное вхождение'


@pytest.mark.asyncio
async def test_list_search(sqlite_sessionmaker):
    category = sqlalchemy.SQLAlchemyAdmin(
        search_fields=['title'],
        model=Terminal,
        db_async_session=sqlite_sessionmaker,
        table_schema=sqlalchemy.SQLAlchemyFieldsSchema(
            model=Terminal,
            fields=['id'],
        ),
    )
    language_manager = CustomLanguageManager('ru')
    user = auth.UserABC(username="test")

    merchant = await MerchantFactory(title="Test merch")
    currency = await CurrencyFactory()
    terminal_1 = await TerminalFactory(title='Test terminal', merchant=merchant, currency=currency)
    terminal_2 = await TerminalFactory(title='Test terminal second', merchant=merchant, currency=currency)
    terminal_3 = await TerminalFactory(title='other', merchant=merchant, currency=currency)
    await TerminalFactory(title='other', merchant=merchant, currency=currency)

    list_result: dict = await category.get_list(
        list_data=schema.ListData(search='Test'),
        user=user,
        language_manager=language_manager,
    )
    assert list_result == schema.TableListResult(data=[{'id': terminal_1.id}, {'id': terminal_2.id}], total_count=2), 'Поиск по title'


@pytest.mark.asyncio
async def test_filter_related(sqlite_sessionmaker):
    category = sqlalchemy.SQLAlchemyAdmin(
        model=Terminal,
        db_async_session=sqlite_sessionmaker,
        table_schema=sqlalchemy.SQLAlchemyFieldsSchema(
            model=Terminal,
            fields=['id'],
        ),
        table_filters=sqlalchemy.SQLAlchemyFieldsSchema(
            model=Terminal,
            fields=['merchant_id'],
        ),
    )
    language_manager = CustomLanguageManager('ru')
    user = auth.UserABC(username="test")

    currency = await CurrencyFactory()

    merchant_1 = await MerchantFactory()
    terminal_1 = await TerminalFactory(merchant=merchant_1, currency=currency)

    merchant_2 = await MerchantFactory()
    terminal_2 = await TerminalFactory(merchant=merchant_2, currency=currency)

    list_result: dict = await category.get_list(
        list_data=schema.ListData(filters={'merchant_id': merchant_2.id}),
        user=user,
        language_manager=language_manager,
    )
    assert list_result == schema.TableListResult(data=[{'id': terminal_2.id}], total_count=1), 'Фильтр по related'


@pytest.mark.asyncio
async def test_list_bad_search_field(sqlite_sessionmaker):
    with pytest.raises(AttributeError) as e:
        sqlalchemy.SQLAlchemyAdmin(
            search_fields=['no_field'],
            model=Terminal,
            db_async_session=sqlite_sessionmaker,
        )

    assert str(e.value) == 'SQLAlchemyAdmin: search field "no_field" not found in model Terminal'


@pytest.mark.asyncio
async def test_ordering(sqlite_sessionmaker):
    category = sqlalchemy.SQLAlchemyAdmin(
        model=Terminal,
        db_async_session=sqlite_sessionmaker,
        ordering_fields=['id'],
        table_schema=sqlalchemy.SQLAlchemyFieldsSchema(
            model=Terminal,
            fields=['id'],
        ),
    )
    language_manager = CustomLanguageManager('ru')
    user = auth.UserABC(username="test")

    currency = await CurrencyFactory()
    merchant = await MerchantFactory()

    terminal_1 = await TerminalFactory(merchant=merchant, currency=currency)
    terminal_2 = await TerminalFactory(merchant=merchant, currency=currency)

    list_result: dict = await category.get_list(
        list_data=schema.ListData(ordering='id'),
        user=user,
        language_manager=language_manager,
    )
    assert list_result == schema.TableListResult(data=[{'id': terminal_1.id}, {'id': terminal_2.id, }], total_count=2), 'сортировка по возрастанию'

    list_result: dict = await category.get_list(
        list_data=schema.ListData(ordering='-id'),
        user=user,
        language_manager=language_manager,
    )
    assert list_result == schema.TableListResult(data=[{'id': terminal_2.id}, {'id': terminal_1.id, }], total_count=2), 'сортировка по убыванию'
