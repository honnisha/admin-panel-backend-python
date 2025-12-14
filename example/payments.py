import datetime
import uuid
from typing import Any, Optional

from faker import Faker

from admin_panel import schema
from admin_panel.schema.table.admin_action import ActionData, ActionMessage, ActionResult, admin_action
from admin_panel.utils import LanguageManager
from admin_panel.utils import TranslateText as _


class PaymentFiltersSchema(schema.FieldsSchema):
    id = schema.IntegerField(label='ID')
    created_at = schema.DateTimeField(label=_('created_at'))

    fields = [
        'id',
        'created_at',
    ]


STATUS_COLORS = {'process': 'gray', 'success': 'green', 'error': 'red'}


class PaymentFieldsSchema(schema.FieldsSchema):
    id = schema.IntegerField(label='ID', read_only=True)
    amount = schema.IntegerField(label=_('amount'))
    endpoint = schema.StringField(label=_('endpoint'))
    description = schema.StringField(label=_('description'))
    status = schema.ChoiceField(
        label=_('status'),
        tag_colors=STATUS_COLORS,
    )
    image = schema.ImageField(label=_('image'))
    created_at = schema.DateTimeField(label=_('created_at'), read_only=True)

    fields = [
        'id',
        'amount',
        'created_at',
        'get_provider_registry',
        'get_provider_registry_info',
    ]

    @schema.function_field(label=_('registry_checked'), type=schema.BooleanField)
    async def get_provider_registry(self, record, **kwargs):
        return await True

    @schema.function_field(label=_('registry_info_checked'), type=schema.BooleanField)
    async def get_provider_registry_info(self, record, **kwargs):
        return await False


class CreatePaymentSchema(schema.FieldsSchema):
    amount = schema.IntegerField(label=_('amount'))


class PaymentsAdmin(schema.CategoryTable):
    slug = 'payments'
    title = _('payments')
    icon = 'mdi-credit-card-outline'

    search_enabled = True
    search_help = _('payments_search_fields')

    table_filters = PaymentFiltersSchema()
    table_schema = PaymentFieldsSchema()
    ordering_fields = [
        'id',
    ]

    @admin_action(
        title=_('create_payment'),
        description=_('create_payment_description'),
        form_schema=CreatePaymentSchema(),
        allow_empty_selection=True,
    )
    async def create_payment(self, action_data: ActionData):
        msg = _('payment_create_result') % {
            'gateway_id': str(uuid.uuid4()),
            'redirect_url': 'https://www.google.com',
        }
        return ActionResult(persistent_message=msg)

    @admin_action(
        title=_('delete'),
        confirmation_text=_('delete_confirmation_text'),
        base_color='red-lighten-2',
        variant='outlined',
    )
    async def delete(self, action_data: ActionData):
        return ActionResult(message=ActionMessage('test'))

    def _get_data(self, pk):
        fake = Faker()
        Faker.seed(pk)

        statuses = list(STATUS_COLORS.keys())
        status = statuses[fake.pyint(min_value=0, max_value=len(statuses) - 1)]
        return {
            'id': pk,
            'amount': 10 * fake.pyint(min_value=0, max_value=100),
            'status': status,
            'endpoint': fake.word(),
            'description': fake.sentence(nb_words=5),
            'image': f'https://picsum.photos/id/{5039-pk+1}/200/300',
            'created_at': datetime.datetime(2025, 6, 16, 9, 45, 29) - datetime.timedelta(hours=pk, minutes=pk),
        }

    # pylint: disable=too-many-arguments
    async def get_list(self, list_data: schema.ListData, user: schema.UserABC, language: LanguageManager) -> schema.TableListResult:
        data = []
        total_count = 5039

        for i in range(0, list_data.limit):
            pk = total_count - ((list_data.page - 1) * list_data.limit + i)
            if pk < 0:
                continue

            line_data = self._get_data(pk)
            line = await self.table_schema.serialize(line_data, extra={'user': user})
            data.append(line)

        return schema.TableListResult(data=data, total_count=total_count)

    async def retrieve(self, pk: Any, user: schema.UserABC) -> Optional[dict]:
        line_data = self._get_data(int(pk))
        line = await self.table_schema.serialize(line_data, extra={'user': user})
        return line

    async def update(self, pk: Any, data: dict, user: schema.UserABC) -> schema.UpdateResult:
        return schema.UpdateResult(pk=0)
