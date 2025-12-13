from typing import Any, Optional
from admin_panel import schema


class PaymentFiltersSchema(schema.FieldsSchema):
    id = schema.IntegerField(label='ID')
    created_at = schema.DateTimeField(label='Created')

    _fields = [
        'id',
        'created_at',
    ]


class PaymentFieldsSchema(schema.FieldsSchema):
    id = schema.IntegerField(label='ID')
    amount = schema.IntegerField(label='Amount')
    created_at = schema.DateTimeField(label='Created')

    _fields = [
        'id',
        'amount',
        'created_at',
        'get_provider_registry',
        'get_provider_registry_info',
    ]
    _readonly_fields = [
        'amount',
        'created_at',
    ]

    @schema.function_field(label='Реестр проверен', type=schema.BooleanField)
    async def get_provider_registry(self, record, **kwargs):
        return await True

    @schema.function_field(label='Информация по реестру провайдера', type=schema.BooleanField)
    async def get_provider_registry_info(self, record, **kwargs):
        return await False


class PaymentsAdmin(schema.CategoryTable):
    slug = 'payments'

    search_enabled = True
    search_help = 'Search fields: id'

    table_filters = PaymentFiltersSchema()
    table_schema = PaymentFieldsSchema()
    ordering_fields = [
        'id',
    ]

    # pylint: disable=too-many-arguments
    async def get_list(self, list_data: schema.ListData, user: schema.UserABC) -> schema.TableListResult:
        return schema.TableListResult(data={})

    async def retrieve(self, pk: Any, user: schema.UserABC) -> Optional[dict]:
        return {}

    async def create(self, data: dict, user: schema.UserABC) -> schema.CreateResult:
        return NotImplementedError()

    async def update(self, pk: Any, data: dict, user: schema.UserABC) -> schema.UpdateResult:
        return NotImplementedError()
