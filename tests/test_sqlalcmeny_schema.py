from unittest import mock

import pytest

from admin_panel.auth import UserABC
from admin_panel import sqlalchemy
from admin_panel.schema.category import CategorySchemaData, FieldSchemaData, FieldsSchemaData, TableInfoSchemaData
from admin_panel.schema.table.table_models import (
    AutocompleteData, AutocompleteResult, CreateResult, ListData, RetrieveResult, TableListResult, UpdateResult)
from example.main import CustomLanguageManager
from example.sections.models import CurrencyFactory, MerchantFactory, Terminal

table_schema_data = FieldsSchemaData(
    list_display=[
        'id',
        'title',
        'description',
        'secret_key',
        'currency_id',
        'merchant_id',
        'is_h2h',
        'registered_delay',
        'created_at',
    ],
    fields={
        'title': FieldSchemaData(
            type='string',
            label='Title',
            max_length=255,
            required=True,
        ),
        'merchant_id': FieldSchemaData(
            type='related',
            label='Merchant',
            read_only=False,
            required=True,
            many=False,
            rel_name='merchant',
        ),
        'currency_id': FieldSchemaData(
            type='related',
            label='Currency',
            read_only=False,
            required=True,
            many=False,
            rel_name='currency',
        ),
        'is_h2h': FieldSchemaData(
            type='boolean',
            label='Is H2H',
            read_only=False,
        ),
        'registered_delay': FieldSchemaData(
            type='integer',
            label='Registered Delay',
        ),
        'id': FieldSchemaData(
            type='integer',
            label='ID',
            read_only=True,
        ),
        'description': FieldSchemaData(
            type='string',
            label='Описание',
            required=True,
            max_length=255,
        ),
        'secret_key': FieldSchemaData(
            type='string',
            label='Secret Key',
            max_length=255,
        ),
        'created_at': FieldSchemaData(
            type='datetime',
            label='Created At',
        ),
    },
)


category_schema_data = CategorySchemaData(
    title='terminal',
    icon=None,
    type='table',
    table_info=TableInfoSchemaData(
        table_schema=table_schema_data,
        search_enabled=True,
        pk_name='id',
        can_retrieve=True,
        can_update=True,
        can_create=True,
        actions={
            'delete': {
                'allow_empty_selection': False,
                'base_color': 'red-lighten-2',
                'confirmation_text': 'Вы уверены, что хотите удалить данные записи?\n'
                'Данное действие нельзя отменить.',
                'description': None,
                'form_schema': None,
                'icon': None,
                'title': 'Удалить',
                'variant': 'outlined',
            },
        },
    ),
)

FIELDS = ['id', 'title', 'description', 'secret_key', 'currency_id', 'merchant_id', 'is_h2h', 'registered_delay', 'created_at']


@pytest.mark.asyncio
async def test_sqlalchemy_table_schema():
    fields_schema = sqlalchemy.SQLAlchemyFieldsSchema(model=Terminal, fields=FIELDS)
    language_manager = CustomLanguageManager('ru')
    new_schema = fields_schema.generate_schema(UserABC(username="test"), language_manager)
    assert new_schema == table_schema_data


@pytest.mark.asyncio
async def test_generate_category_schema(sqlite_sessionmaker):
    category = sqlalchemy.SQLAlchemyAdmin(
        model=Terminal,
        db_async_session=sqlite_sessionmaker,
        table_schema=sqlalchemy.SQLAlchemyFieldsSchema(model=Terminal, fields=FIELDS),
    )
    language_manager = CustomLanguageManager('ru')
    new_schema = category.generate_schema(UserABC(username="test"), language_manager)
    assert new_schema == category_schema_data


@pytest.mark.asyncio
async def test_create(sqlite_sessionmaker):
    category = sqlalchemy.SQLAlchemyAdmin(
        model=Terminal,
        db_async_session=sqlite_sessionmaker,
        table_schema=sqlalchemy.SQLAlchemyFieldsSchema(model=Terminal, fields=FIELDS)
    )
    language_manager = CustomLanguageManager('ru')

    user = UserABC(username="test")

    merchant = await MerchantFactory(
        title='Test merch',
    )
    currency = await CurrencyFactory()

    create_data = {
        'merchant_id': merchant.id,
        'currency_id': currency.id,
        'description': 'test',
        'title': 'test',
    }
    create_result: CreateResult = await category.create(
        data=create_data,
        user=user,
        language_manager=language_manager,
    )
    assert create_result.pk == 1

    retrieve_result = await category.retrieve(
        pk=create_result.pk,
        user=user,
        language_manager=language_manager,
    )
    expected_data = RetrieveResult(data={
        'created_at': mock.ANY,
        'description': 'test',
        'currency_id': {
            'key': 1,
            'title': "<Currency(id=1, num_code='100', char_code='C000')>",
        },
        'title': 'test',
        'id': 1,
        'is_h2h': True,
        'merchant_id': {'key': 1, 'title': "<Merchant(id=1, title='Test merch')>"},
        'registered_delay': None,
        'secret_key': mock.ANY,
    })
    assert retrieve_result == expected_data

    list_result: dict = await category.get_list(
        list_data=ListData(),
        user=user,
        language_manager=language_manager,
    )
    expected_create = TableListResult(
        data=[
            expected_data.data,
        ],
        total_count=1,
    )
    assert list_result == expected_create

    new_merchant = await MerchantFactory()
    update_data = {
        'merchant_id': new_merchant.id,
        'description': 'new description',
    }
    update_result = await category.update(
        pk=create_result.pk,
        data=update_data,
        user=user,
        language_manager=language_manager,
    )
    assert update_result == UpdateResult(pk=create_result.pk)


@pytest.mark.asyncio
async def test_autocomplete(sqlite_sessionmaker):
    category = sqlalchemy.SQLAlchemyAdmin(model=Terminal, db_async_session=sqlite_sessionmaker)
    language_manager = CustomLanguageManager('ru')

    user = UserABC(username="test")
    autocomplete_result = await category.autocomplete(
        data=AutocompleteData(
            field_slug='merchant_id',
        ),
        user=user,
        language_manager=language_manager,
    )
    assert autocomplete_result == AutocompleteResult()
