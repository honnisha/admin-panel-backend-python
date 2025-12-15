from typing import Any

from pydantic.dataclasses import dataclass

from admin_panel.auth import UserABC
from admin_panel.schema.table.fields.base import TableField
from admin_panel.schema.table.table_models import Record
from admin_panel.translations import LanguageManager
from admin_panel.utils import DeserializeAction


@dataclass
class DjangoRelatedField(TableField):
    queryset: Any = None
    many: bool = False
    _type: str = 'related'

    def generate_schema(self, user: UserABC, field_slug, language: LanguageManager) -> dict:
        schema = super().generate_schema(user, field_slug, language)
        schema['many'] = self.many
        return schema

    async def serialize(self, value, *args, **kwargs) -> Any:
        from asgiref.sync import sync_to_async  # pylint: disable=import-outside-toplevel

        if value:
            return {'key': value.pk, 'title': await sync_to_async(value.__str__)()}

    def get_queryset(self, model, data):
        if self.queryset is not None:
            return self.queryset

        if not model:
            raise AttributeError('ForeignKey must provide queryset in case non model views!')

        # pylint: disable=protected-access
        model_field = model._meta.get_field(data.field_slug)
        target_model = model_field.remote_field.model
        return target_model.objects.all()

    async def autocomplete(self, model, data, user):
        from asgiref.sync import sync_to_async  # pylint: disable=import-outside-toplevel

        results = []

        qs = self.get_queryset(model, data)[:data.limit]
        if data.search_string:
            qs = qs.filter(id=data.search_string)

        if data.existed_choices:
            existed_choices = [i['key'] for i in data.existed_choices]

            # Добавляет в результат уже выбранные варианты
            filter_pks = qs.model.objects.filter(pk__in=existed_choices)
            qs = qs.union(filter_pks)

        async for record in qs:
            results.append(Record(key=record.pk, title=await sync_to_async(record.__str__)()))

        return results

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def set_deserialized_value(self, result: dict, field_slug, deserialized_value, action, extra):
        model = extra['model']
        # pylint: disable=protected-access
        pk_name = model._meta.get_field(field_slug).remote_field.model._meta.pk.name
        result[f'{field_slug}_{pk_name}'] = deserialized_value

    async def deserialize(self, value, action: DeserializeAction, extra: dict, *args, **kwargs) -> Any:
        value = await super().deserialize(value, action, extra, *args, **kwargs)
        if value:
            return value['key']
