import datetime
from typing import Any

from admin_panel import schema
from admin_panel.integrations.sqlalchemy.fields import SQLAlchemyRelatedField
from admin_panel.schema.table.fields.base import DateTimeField
from admin_panel.utils import humanize_field_name


class SQLAlchemyFieldsSchema(schema.FieldsSchema):
    model: Any

    def __init__(self, *args, model=None, **kwargs):
        if model:
            self.model = model

        super().__init__(*args, **kwargs)

    def generate_fields(self, kwargs) -> dict:
        generated_fields = super().generate_fields(kwargs)

        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect
        from sqlalchemy.dialects.postgresql import ARRAY
        from sqlalchemy.ext.mutable import Mutable
        from sqlalchemy.sql import sqltypes
        from sqlalchemy.sql.schema import Column

        mapper = inspect(self.model).mapper

        for attr in mapper.column_attrs:
            col: Column = attr.columns[0]
            field_slug = attr.key

            if field_slug in generated_fields:
                continue

            field_data = {}
            info = col.info or {}
            field_data["label"] = info.get('label', humanize_field_name(field_slug))
            field_data["help_text"] = info.get('help_text')

            field_data["read_only"] = col.primary_key

            # Whether the field is required on input (best-effort heuristic)
            field_data["required"] = (
                not col.nullable
                and col.default is None
                and col.server_default is None
                and not col.primary_key
            )

            if "choices" in info:
                field_data["choices"] = [(c[0], c[1]) for c in info["choices"]]

            col_type = col.type
            try:
                py_t = col_type.python_type
            except Exception:
                py_t = None

            impl = getattr(attr, 'impl', None)
            is_mutable = isinstance(impl, Mutable)

            # Foreign key column
            if col.foreign_keys:
                field_class = SQLAlchemyRelatedField

                # Find relationship that uses this FK column
                rel_name = None
                for rel in mapper.relationships:
                    if col in rel.local_columns:
                        rel_name = rel.key
                        break

                if rel_name:
                    field_data["label"] = info.get('label', humanize_field_name(rel_name))
                    field_data["rel_name"] = rel_name

            elif isinstance(col_type, (sqltypes.BigInteger, sqltypes.Integer)) or py_t is int:
                field_class = schema.IntegerField

            elif isinstance(col_type, sqltypes.Numeric):
                field_class = schema.IntegerField
                field_data["inputmode"] = "decimal"
                field_data["precision"] = col_type.precision
                field_data["scale"] = col_type.scale

            elif isinstance(col_type, sqltypes.String) or py_t is str:
                field_class = schema.StringField
                # Max length is usually stored as String(length=...)
                if getattr(col_type, "length", None):
                    field_data["max_length"] = col_type.length

            elif isinstance(col_type, sqltypes.DateTime) or py_t is datetime:
                field_class = schema.DateTimeField

            elif isinstance(col_type, sqltypes.Boolean) or py_t is bool:
                field_class = schema.BooleanField

            elif isinstance(col_type, sqltypes.JSON):
                field_class = schema.JSONField

            elif isinstance(col_type, ARRAY):
                field_class = schema.ArrayField
                field_data["array_type"] = type(col_type.item_type).__name__.lower()
                field_data["read_only"] = not is_mutable

            elif isinstance(col_type, sqltypes.NullType):
                continue

            elif not self.fields:
                msg = f'SQLAlchemy autogenerate ORM field {self.model.__name__}.{field_slug} is not supported for type: {col_type}'
                raise AttributeError(msg)

            schema_field = field_class(**field_data)

            if col.primary_key:
                generated_fields = {field_slug: schema_field, **generated_fields}
            else:
                generated_fields[field_slug] = schema_field

        for rel in mapper.relationships:
            field_slug = rel.key

            if field_slug in generated_fields:
                continue

            field_data = {}

            info = rel.info or {}
            field_data["label"] = info.get('label', humanize_field_name(field_slug))
            field_data["help_text"] = info.get('help_text')

            field_data["read_only"] = False
            field_data["required"] = False

            field_data["many"] = rel.uselist

            field_class = SQLAlchemyRelatedField

            generated_fields[field_slug] = field_class(**field_data)

        return generated_fields

    def apply_filters(self, stmt, filters: dict):
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import String, cast
        from sqlalchemy.orm import InstrumentedAttribute

        # filters
        for field_slug, value in filters.items():
            field = self.get_field(field_slug)

            if not field:
                available_filters = list(self.get_fields().keys())
                msg = f'{type(self).__name__} filter "{field_slug}" not found inside table_filters fields: {available_filters}'
                raise AttributeError(msg)

            column = getattr(self.model, field_slug, None)

            if issubclass(type(field), DateTimeField) and field.range:
                if not isinstance(value, dict) or not value.get('from') or not value.get('to'):
                    msg = f'{type(self).__name__} filter "{field_slug}" value must be dict with from,to values'
                    raise AttributeError(msg)

                stmt = stmt.where(column >= datetime.datetime.fromisoformat(value['from']))
                stmt = stmt.where(column <= datetime.datetime.fromisoformat(value['to']))
                continue

            if not isinstance(column, InstrumentedAttribute):
                msg = f'{type(self).__name__} filter "{field_slug}" not found as field inside model {self.model}'
                raise AttributeError(msg)

            if isinstance(value, list):
                stmt = stmt.where(column.in_(value))

            elif isinstance(value, str):
                stmt = stmt.where(
                    cast(column, String).like(f"%{value}%")
                )

            else:
                stmt = stmt.where(column == value)

        return stmt

    async def serialize(self, line_data: dict, extra: dict, *args, **kwargs) -> dict:
        for field_slug, field in self.get_fields().items():
            # pylint: disable=protected-access
            if field._type == 'function_field':
                continue

            line_data[field_slug] = line_data.get(field_slug)

        return await super().serialize(line_data, extra, *args, **kwargs)
