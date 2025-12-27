from typing import Any

from admin_panel.integrations.sqlalchemy.autocomplete import SQLAlchemyAdminAutocompleteMixin
from admin_panel.integrations.sqlalchemy.fields_schema import SQLAlchemyFieldsSchema
from admin_panel.schema.table.category_table import CategoryTable
from admin_panel.translations import TranslateText as _


def record_to_dict(record):
    # pylint: disable=import-outside-toplevel
    from sqlalchemy import inspect
    return {
        attr.key: getattr(record, attr.key)
        for attr in inspect(record).mapper.column_attrs
    }


class SQLAlchemyAdminBase(SQLAlchemyAdminAutocompleteMixin, CategoryTable):
    model: Any
    slug = None
    ordering_fields = []

    search_fields = []

    table_schema: SQLAlchemyFieldsSchema

    db_async_session: Any = None

    def __init__(
            self,
            *args,
            model=None,
            db_async_session=None,
            ordering_fields=None,
            search_fields=None,
            **kwargs,
    ):
        if model:
            self.model = model

        if search_fields:
            self.search_fields = search_fields

        if self.search_fields:
            self.search_enabled = True
            self.search_help = _('search_help') % {'fields': ', '.join(self.search_fields)}
            self.validate_search_fields()

        if not self.table_schema:
            self.table_schema = SQLAlchemyFieldsSchema(model=self.model)

        if not issubclass(type(self.table_schema), SQLAlchemyFieldsSchema):
            msg = f'{type(self).__name__}.table_schema {self.table_schema} must be subclass of SQLAlchemyFieldsSchema'
            raise AttributeError(msg)

        stmt = self.get_queryset()
        if not self.model and stmt:
            model = stmt.column_descriptions[0]["entity"]

        if not self.model:
            msg = f'{type(self).__name__}.model is required for SQLAlchemy'
            raise AttributeError(msg)

        if not self.slug:
            self.slug = self.model.__name__.lower()

        if db_async_session:
            self.db_async_session = db_async_session

        if not self.db_async_session:
            msg = f'{type(self).__name__}.db_async_session is required for SQLAlchemy'
            raise AttributeError(msg)

        if ordering_fields:
            self.ordering_fields = ordering_fields

        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect
        from sqlalchemy.sql.schema import Column

        for attr in inspect(self.model).mapper.column_attrs:
            col: Column = attr.columns[0]
            if col.primary_key and not self.pk_name:
                self.pk_name = attr.key
                break

        super().__init__(*args, **kwargs)

    def validate_search_fields(self):
        if not self.search_fields:
            return

        # pylint: disable=import-outside-toplevel
        from sqlalchemy.orm import InstrumentedAttribute

        for field in self.search_fields:
            column = getattr(self.model, field, None)
            if not isinstance(column, InstrumentedAttribute):
                raise AttributeError(
                    f'{type(self).__name__}: search field "{field}" not found in model {self.model.__name__}'
                )


    def get_queryset(self):
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        stmt = select(self.model).options(selectinload('*'))

        # Eager-load related fields
        for slug, field in self.table_schema.get_fields().items():

            # pylint: disable=protected-access
            if field._type == "related" and field.rel_name:

                if not hasattr(self.model, field.rel_name):
                    msg = (
                        f'Model {self.model.__name__} do not contain rel_name:"{field.rel_name} '
                        f'for field "{slug}" {field}'
                    )
                    raise AttributeError(msg)

                if field.rel_name:
                    stmt = stmt.options(selectinload(getattr(self.model, field.rel_name)))

        return stmt
