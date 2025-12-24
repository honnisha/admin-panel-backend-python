import uuid
from datetime import datetime
from unittest import mock

import pytest
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from admin_panel.auth import UserABC
from admin_panel.integrations.sqlalchemy.table import SQLAlchemyAdmin, SQLAlchemyFieldsSchema
from admin_panel.schema.category import CategorySchemaData, FieldSchemaData, FieldsSchemaData, TableInfoSchemaData
from admin_panel.schema.table.table_models import (
    AutocompleteData, AutocompleteResult, CreateResult, ListData, TableListResult, UpdateResult)
from admin_panel.translations import TranslateText as _
from example.main import CustomLanguageManager
from tests.conftest import ModelBase


class BusinessBaseModel(ModelBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class Merchant(BusinessBaseModel):
    __tablename__ = "merchant"

    terminals: Mapped[list["Terminal"]] = relationship(back_populates="merchant")


class Terminal(BusinessBaseModel):
    __tablename__ = "terminal"

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        info={"label": _("description")},
    )
    secret_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )

    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchant.id"), index=True)

    is_h2h: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.true())

    registered_delay: Mapped[int | None] = mapped_column(Integer, nullable=True)

    merchant: Mapped["Merchant"] = relationship(back_populates="terminals")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # DateTime used once

    # whitelist_ips: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)


table_schema_data = FieldsSchemaData(
    list_display=[
        'description',
        'secret_key',
        'merchant_id',
        'is_h2h',
        'registered_delay',
        'created_at',
        'id',
    ],
    fields={
        'merchant_id': FieldSchemaData(
            type='related',
            label='Merchant ID',
            read_only=False,
            required=True,
            many=False,
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


@pytest.mark.asyncio
async def test_sqlalchemy_table_schema():
    fields_schema = SQLAlchemyFieldsSchema(model=Terminal)
    language_manager = CustomLanguageManager('ru')
    new_schema = fields_schema.generate_schema(UserABC(username="test"), language_manager)
    assert new_schema == table_schema_data


@pytest.mark.asyncio
async def test_generate_category_schema(sqlite_sessionmaker):
    category = SQLAlchemyAdmin(model=Terminal, db_async_session=sqlite_sessionmaker)
    language_manager = CustomLanguageManager('ru')
    new_schema = category.generate_schema(UserABC(username="test"), language_manager)
    assert new_schema == category_schema_data


@pytest.mark.asyncio
async def test_create(sqlite_sessionmaker):
    category = SQLAlchemyAdmin(model=Terminal, db_async_session=sqlite_sessionmaker)
    language_manager = CustomLanguageManager('ru')

    user = UserABC(username="test")

    create_data = {
        'merchant_id': 1,
        'description': 'test',
    }
    create_result: CreateResult = await category.create(
        data=create_data,
        user=user,
        language_manager=language_manager,
    )
    assert create_result.pk == 1

    retrieve_result: dict = await category.retrieve(
        pk=create_result.pk,
        user=user,
        language_manager=language_manager,
    )
    expected_data = {
        'created_at': mock.ANY,
        'description': 'test',
        'id': 1,
        'is_h2h': True,
        'merchant_id': {'key': 1, 'title': '1'},
        'registered_delay': None,
        'secret_key': mock.ANY,
    }
    assert retrieve_result == expected_data

    list_result: dict = await category.get_list(
        list_data=ListData(),
        user=user,
        language_manager=language_manager,
    )
    expected_create = TableListResult(
        data=[
            expected_data
        ],
        total_count=1,
    )
    assert list_result == expected_create

    update_data = {
        'description': 'new description',
        'merchant_id': 3,
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
    category = SQLAlchemyAdmin(model=Terminal, db_async_session=sqlite_sessionmaker)
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
