from dataclasses import dataclass
from typing import Any

from asgiref.sync import sync_to_async

from admin_panel.schema.table.fields.base import TableField
from admin_panel.schema.table.fields.deserialize_action_types import DeserializeAction
from admin_panel.schema.table.table_models import Record


@dataclass
class ForeignKey(TableField):
    _type: str = 'foreign_key'

    async def serialize(self, value, *args, **kwargs) -> Any:
        if value:
            return {'key': value.pk, 'title': await sync_to_async(value.__str__)()}

    async def autocomplete(self, model, data):
        model_field = model._meta.get_field(data.field_slug)
        target_model = model_field.remote_field.model

        results = []

        qs = target_model.objects.all()[:data.limit]
        if data.search_string:
            qs = qs.filter(id=data.search_string)

        if data.existed_choices:
            existed_choices = [i['key'] for i in data.existed_choices]

            # Добавляет в результат уже выбранные варианты
            filter_pks = target_model.objects.filter(pk__in=existed_choices)
            qs = qs.union(filter_pks)

        async for record in qs:
            results.append(Record(key=record.pk, title=await sync_to_async(record.__str__)()))

        return results

    # pylint: disable=too-many-arguments
    def set_deserialized_value(self, result: dict, field_slug, deserialized_value, action, extra):
        model = extra['model']
        pk_name = model._meta.get_field(field_slug).remote_field.model._meta.pk.name
        result[f'{field_slug}_{pk_name}'] = deserialized_value

    async def deserialize(self, value, action: DeserializeAction, extra: dict, *args, **kwargs) -> Any:
        value = await super().deserialize(value, action, extra, *args, **kwargs)
        if value:
            return value['key']
