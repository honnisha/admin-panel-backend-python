from datetime import datetime

import pytest
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from admin_panel.auth import UserABC
from admin_panel.integrations.sqlalchemy.table import SQLAlchemyAdminBase, SQLAlchemyFieldsSchema
from admin_panel.schema.category import CategorySchemaData, FieldSchemaData, FieldsSchemaData, TableInfoSchemaData
from admin_panel.translations import TranslateText as _
from example.main import CustomLanguageManager


class BusinessBase(DeclarativeBase):
    pass


class BusinessBaseModel(BusinessBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


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
    secret_key: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("gen_random_uuid()"))

    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchant.id"), index=True)

    is_h2h: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.true())

    registered_delay: Mapped[int | None] = mapped_column(Integer, nullable=True)

    merchant: Mapped["Merchant"] = relationship(back_populates="terminals")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # DateTime used once

    whitelist_ips: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)


table_schema_data = FieldsSchemaData(
    list_display=[
        'description',
        'secret_key',
        'merchant_id',
        'is_h2h',
        'registered_delay',
        'created_at',
        'whitelist_ips',
        'id',
    ],
    fields={
        'merchant_id': FieldSchemaData(
            type='related',
            label='Merchant ID',
            read_only=False,
            required=True,
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
        'whitelist_ips': FieldSchemaData(
            type='array',
            label='Whitelist Ips',
            array_type='string',
        ),
    }
)


category_schema_data = CategorySchemaData(
    title='terminal',
    icon=None,
    type='table',
    table_info=TableInfoSchemaData(
        table_schema=table_schema_data,
        pk_name='id',
        can_retrieve=True,
    ),
)


@pytest.mark.asyncio
async def test_sqlalchemy_table_schema():
    fields_schema = SQLAlchemyFieldsSchema(model=Terminal)
    language_manager = CustomLanguageManager('ru')
    new_schema = fields_schema.generate_schema(UserABC(username="test"), language_manager)
    assert new_schema == table_schema_data


@pytest.mark.asyncio
async def test_generate_category_schema():
    category = SQLAlchemyAdminBase(model=Terminal)
    language_manager = CustomLanguageManager('ru')
    new_schema = category.generate_schema(UserABC(username="test"), language_manager)
    assert new_schema == category_schema_data
