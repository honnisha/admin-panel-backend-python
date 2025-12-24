from typing import Any, List

from pydantic.dataclasses import dataclass

from admin_panel.auth import UserABC
from admin_panel.schema.category import FieldSchemaData
from admin_panel.schema.table.fields.base import TableField
from admin_panel.schema.table.table_models import Record
from admin_panel.translations import LanguageManager
from admin_panel.utils import DeserializeAction


@dataclass
class SQLAlchemyRelatedField(TableField):
    _type: str = 'related'
    queryset: Any = None  # optional custom query builder
    many: bool = False
    rel_name: str | None = None

    def generate_schema(self, user: UserABC, field_slug, language_manager: LanguageManager) -> FieldSchemaData:
        schema = super().generate_schema(user, field_slug, language_manager)
        schema.many = self.many
        schema.rel_name = self.rel_name
        return schema

    def _get_target_model(self, model, field_slug):
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import inspect

        mapper = inspect(model).mapper
        attr = mapper.attrs.get(field_slug)
        if attr is None:
            msg = f'Field "{field_slug}" is not found on model "{model}"'
            raise Exception(msg)

        # RelationshipProperty
        if hasattr(attr, 'mapper'):
            return attr.mapper.class_

        # ColumnProperty (FK column). Try to resolve from foreign key target table.
        col = getattr(model, field_slug).property.columns[0]
        if not col.foreign_keys:
            msg = f'Field "{field_slug}" is not a relationship and not a FK column'
            raise Exception(msg)

        fk = next(iter(col.foreign_keys))
        target_table = fk.column.table

        # Find a mapped class that uses this table in the same registry
        for m in mapper.registry.mappers:
            if getattr(m, 'local_table', None) is target_table:
                return m.class_

        msg = f'Cannot resolve target model for FK "{field_slug}"'
        raise Exception(msg)

    def get_queryset(self, model, data, session):
        # Allow overriding query logic
        if self.queryset is not None:
            return self.queryset(model, data, session)

        if not model:
            msg = 'Related field must provide queryset in case non model views!'
            raise AttributeError(msg)

        target_model = self._get_target_model(model, data.field_slug)
        # Return target model + session; actual select is built in autocomplete
        return target_model

    async def autocomplete(self, model, data, user, *, extra: dict | None = None) -> List[Record]:
        # pylint: disable=import-outside-toplevel
        from sqlalchemy import select
        from sqlalchemy.sql import expression

        if extra is None or extra.get('db_session') is None:
            msg = f'SQLAlchemyRelatedField.autocomplete {type(self).__name__} requires extra["db_session"] (AsyncSession)'
            raise AttributeError(msg)

        session = extra['db_session']

        results = []

        target_model = self.get_queryset(model, data, session)
        stmt = select(target_model).limit(data.limit)

        # Keep behaviour similar to Django version: search by id if search_string exists
        if data.search_string:
            if hasattr(target_model, 'id'):
                stmt = stmt.where(getattr(target_model, 'id') == data.search_string)

        # Add already selected choices
        existed_choices = []
        if data.existed_choices:
            existed_choices = [i['key'] for i in data.existed_choices if 'key' in i]

        if existed_choices and hasattr(target_model, 'id'):
            stmt = stmt.where(getattr(target_model, 'id').in_(existed_choices) | expression.true())

        records = (await session.execute(stmt)).scalars().all()
        for record in records:
            results.append(Record(key=getattr(record, 'id'), title=str(record)))

        return results

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        # `value` may be a related ORM instance (via relationship) or a raw FK id.
        if value is None:
            return None

        if self.rel_name:
            record = getattr(extra['record'], self.rel_name)
            if record:
                return {'key': value, 'title': str(record)}

        # Otherwise assume scalar key
        return {'key': value, 'title': str(value)}

    async def deserialize(self, value, action: DeserializeAction, extra: dict, *args, **kwargs) -> Any:
        value = await super().deserialize(value, action, extra, *args, **kwargs)
        if not value:
            return None

        if isinstance(value, dict) and 'key' in value:
            return value['key']

        return value
