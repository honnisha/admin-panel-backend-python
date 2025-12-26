import logging

from admin_panel.auth import UserABC
from admin_panel.schema.table import CategoryTable
from admin_panel.schema.table import fields as schema_fields
from admin_panel.schema.table.admin_action import ActionData, ActionMessage, ActionResult, admin_action
from admin_panel.schema.table.fields.function_field import FunctionField
from admin_panel.schema.table.fields_schema import FieldsSchema
from admin_panel.schema.table.table_models import CreateResult, ListData, RetrieveResult, TableListResult, UpdateResult
from admin_panel.translations import LanguageManager
from admin_panel.utils import DeserializeAction

from .autocomplete import DjangoAdminAutocomplete
from .fields import DjangoRelatedField

logger = logging.getLogger('admin_panel')


def fix_str(value):
    if value.__class__.__name__ == '__proxy__':
        return str(value)
    return value


class DjangoFieldsSchema(FieldsSchema):
    model = None

    def __init__(self):

        super().__init__()

        model = getattr(self, 'model', None)
        if not model:
            msg = f'Class {self.__class__} must have model'
            raise AttributeError(msg)

        added_fields = []
        for field in model._meta.fields:

            name = getattr(field, 'name', None) or getattr(field, 'attname', None)
            if self.fields and name not in self.fields:
                continue

            field_data = {}
            field_data['label'] = fix_str(field.verbose_name)
            field_data['help_text'] = fix_str(field.help_text)

            if field.choices:
                field_data['choices'] = [(fix_str(c[1]), fix_str(c[1])) for c in field.choices]

            if field.__class__.__name__ in ['BigAutoField', 'BigIntegerField']:
                field_class = schema_fields.IntegerField
                field_data['help_text'] = field.max_length

            elif field.__class__.__name__ in ['CharField', 'URLField']:
                field_class = schema_fields.StringField
                field_data['max_length'] = field.max_length

            elif field.__class__.__name__ == 'ForeignKey':
                field_data['required'] = not field.null
                field_class = DjangoRelatedField

            elif field.__class__.__name__ == 'DateTimeField':
                field_class = schema_fields.DateTimeField

            elif field.__class__.__name__ == 'BooleanField':
                field_class = schema_fields.BooleanField

            elif field.__class__.__name__ == 'JSONField':
                field_class = schema_fields.JSONField

            else:
                print('field', field.__dict__)
                print('Django ORM field %s is not supported: %s', field.__class__, field)
                continue

            if field.primary_key and name == model._meta.pk.name:
                field_data['read_only'] = True
                field_data['header'] = {'fixed': True, 'width': 50, 'minWidth': 50}

            schema_field = field_class(**field_data)
            setattr(self, name, schema_field)
            added_fields.append(name)

        if not self.fields:
            self.fields = added_fields


class DjangoDeleteAction:
    @admin_action(title='Delete', confirmation_text='Are you sure?')
    async def delete(self, action_data: ActionData):
        return ActionResult(message=ActionMessage('test'))


class DjangoAdminBase(DjangoAdminAutocomplete, CategoryTable):
    queryset = None
    model = None

    def get_queryset(self):
        return self.queryset

    def get_model(self):
        if self.model:
            return self.model
        return self.get_queryset().model

    def __init__(self):
        if not self.pk_name:
            self.pk_name = self.get_model()._meta.pk.name

        if not self.slug:
            self.slug = self.get_model().__name__.lower()

        super().__init__()

        if not self.title:
            self.title = fix_str(self.get_model()._meta.verbose_name_plural)

    async def get_list(self, list_data: ListData, user: UserABC, language_manager: LanguageManager) -> TableListResult:
        from asgiref.sync import sync_to_async  # pylint: disable=import-outside-toplevel

        data = []
        qs = self.get_queryset()
        total_count = await qs.acount()
        async for record in qs:
            line_data = {}
            for field_slug, field in self.table_schema.get_fields().items():

                if issubclass(field.__class__, FunctionField):
                    continue

                line_data[field_slug] = await sync_to_async(getattr)(record, field_slug)

            line = await self.table_schema.serialize(line_data, extra={'record': record, 'user': user})
            data.append(line)

        return TableListResult(
            data=data,
            total_count=total_count,
        )

    async def retrieve(self, pk, user: UserABC) -> RetrieveResult:
        from asgiref.sync import sync_to_async  # pylint: disable=import-outside-toplevel

        assert self.pk_name
        record = await self.get_queryset().filter(**{self.pk_name: pk}).afirst()
        if record is None:
            return None

        line_data = {}
        for field_slug, field in self.table_schema.get_fields().items():

            if issubclass(field.__class__, FunctionField):
                continue

            line_data[field_slug] = await sync_to_async(getattr)(record, field_slug)

        data = await self.table_schema.serialize(line_data, extra={'record': record, 'user': user})
        return RetrieveResult(data=data)


class DjangoAdminCreate:
    async def create(self, data: dict, user: UserABC) -> CreateResult:
        deserialized_data = await self.table_schema.deserialize(
            data,
            action=DeserializeAction.CREATE,
            extra={'model': self.get_model(), 'user': user},
        )

        record = await self.get_model().objects.acreate(**deserialized_data)
        return CreateResult(pk=record.pk)


class DjangoAdminUpdate:
    async def update(self, pk, data: dict, user: UserABC) -> UpdateResult:
        pk = data.get(self.pk_name)
        qs = self.get_model().objects.filter(pk=pk)
        if not await qs.aexists():
            return None

        record = await qs.afirst()

        deserialized_data = await self.table_schema.deserialize(
            data,
            action=DeserializeAction.UPDATE,
            extra={'record': record, 'model': self.get_model(), 'user': user}
        )

        for k, v in deserialized_data.items():
            setattr(record, k, v)

        await record.asave(update_fields=deserialized_data.keys())
        return UpdateResult(pk=pk)
