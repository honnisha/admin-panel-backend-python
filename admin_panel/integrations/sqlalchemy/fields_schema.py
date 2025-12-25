import datetime
from typing import Any

from admin_panel import schema
from admin_panel.integrations.sqlalchemy.fields import SQLAlchemyRelatedField
from admin_panel.utils import humanize_field_name


class SQLAlchemyFieldsSchema(schema.FieldsSchema):
    model: Any

    def __init__(self, model=None, *args, **kwargs):
        if model:
            self.model = model

        super().__init__(*args, **kwargs)

    def post_init(self, *args, **kwargs):
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect
        from sqlalchemy.dialects.postgresql import ARRAY
        from sqlalchemy.sql import sqltypes
        from sqlalchemy.sql.schema import Column

        mapper = inspect(self.model).mapper
        added_fields = []
        for attr in mapper.column_attrs:
            col: Column = attr.columns[0]
            name = attr.key

            if self.fields and name not in self.fields:
                continue

            field_data = {}
            info = col.info or {}
            field_data["label"] = info.get('label', humanize_field_name(name))
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

            elif isinstance(col_type, sqltypes.NullType):
                continue

            else:
                msg = f'SQLAlchemy autogenerate ORM field "{name}" is not supported for type: {col_type}'
                raise AttributeError(msg)

            schema_field = field_class(**field_data)
            setattr(self, name, schema_field)
            added_fields.append(name)

        if not self.fields:
            self.fields = added_fields

        super().post_init(*args, **kwargs)

    async def serialize(self, line_data: dict, extra: dict, *args, **kwargs) -> dict:
        for field_slug, field in self.get_fields().items():
            # pylint: disable=protected-access
            if field._type == 'function_field':
                continue

            line_data[field_slug] = line_data.get(field_slug)

        return await super().serialize(line_data, extra, *args, **kwargs)
