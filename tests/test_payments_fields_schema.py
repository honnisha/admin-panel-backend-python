import pytest

from admin_panel.auth import UserABC
from admin_panel.schema.category import CategorySchemaData, FieldSchemaData, FieldsSchemaData, TableInfoSchemaData
from example.main import CustomLanguageManager
from example.sections.payments import PaymentFieldsSchema, PaymentsAdmin

table_schema_data = FieldsSchemaData(
    list_display=[
        'id',
        'amount',
        'endpoint',
        'status',
        'description',
        'created_at',
        'get_provider_registry',
        'get_provider_registry_info',
    ],
    fields={
        'id': FieldSchemaData(
            type='integer',
            label='ID',
            read_only=True,
        ),
        'amount': FieldSchemaData(
            type='integer',
            label='Сумма',
            read_only=True,
        ),
        'endpoint': FieldSchemaData(
            type='string',
            label='Эндпоинт',
        ),
        'status': FieldSchemaData(
            type='choice',
            label='Статус',
            choices=[
                {'value': 'process', 'title': 'Process'},
                {'value': 'success', 'title': 'Success'},
                {'value': 'error', 'title': 'Error'},
            ],
            tag_colors={'process': 'grey-lighten-1', 'success': 'green-darken-1', 'error': 'red-lighten-2'},
            variant='elevated',
            size='default',
        ),
        'description': FieldSchemaData(
            type='string',
            label='Описание',
        ),
        'created_at': FieldSchemaData(
            type='datetime',
            label='Время создания',
            read_only=True,
        ),
        'get_provider_registry': FieldSchemaData(
            type='boolean',
            label='Реестр проверен',
            read_only=True,
        ),
        'get_provider_registry_info': FieldSchemaData(
            type='boolean',
            label='Информация по реестру провайдера',
            read_only=True,
        ),
        'other_field': FieldSchemaData(
            type='string',
            label='other_field',
            read_only=True,
        ),
        'whitelist_ips': FieldSchemaData(
            type='array',
            label='Белый список IP',
        ),
    },
)

table_filtes = FieldsSchemaData(
    fields={
        'id': FieldSchemaData(
            type='integer',
            label='ID',
        ),
        'created_at': FieldSchemaData(
            type='datetime',
            label='Время создания',
        ),
    },
    list_display=['id', 'created_at'],
)

category_schema_data = CategorySchemaData(
    title='Платежи',
    icon='mdi-credit-card-outline',
    type='table',
    table_info=TableInfoSchemaData(
        table_schema=table_schema_data,
        pk_name='id',
        can_retrieve=True,
        can_update=True,
        search_enabled=True,
        can_create=True,
        search_help='Доступные поля для поиска: id',
        ordering_fields=['id'],
        table_filters=table_filtes,
        actions={
            'action_with_exception': {
                'allow_empty_selection': True,
                'base_color': None,
                'confirmation_text': None,
                'description': None,
                'form_schema': None,
                'icon': None,
                'title': 'Действие с ошибкой',
                'variant': None,
            },
            'create_payment': {
                'allow_empty_selection': True,
                'base_color': None,
                'confirmation_text': None,
                'description': 'Создать платеж и отправить его на обработку в платежную систему.',
                'form_schema': FieldsSchemaData(
                    fields={
                        'amount': FieldSchemaData(
                            type='integer',
                            label='Сумма',
                        ),
                        'is_throw_error': FieldSchemaData(
                            type='boolean',
                            label='Выбросить ошибку?',
                        ),
                    },
                    list_display=[
                        'amount',
                        'is_throw_error',
                    ],
                ),
                'icon': None,
                'title': 'Создать платеж',
                'variant': None,
            },
            'delete': {
                'allow_empty_selection': False,
                'base_color': 'red-lighten-2',
                'confirmation_text': 'Вы уверены, что хотите удалить данные записи?\n'
                'Данное действие нельзя отменить.',
                'description': None,
                'form_schema': None,
                'icon': None,
                'title': 'Удалить',
                'variant': 'outlined',
            },
        },
    ),
)


@pytest.mark.asyncio
async def test_payments_schema(mocker):
    fields_schema = PaymentFieldsSchema()
    language_manager = CustomLanguageManager('ru')
    new_schema = fields_schema.generate_schema(UserABC(username="test"), language_manager)
    assert new_schema == table_schema_data


@pytest.mark.asyncio
async def test_generate_category_schema():
    category = PaymentsAdmin()
    language_manager = CustomLanguageManager('ru')
    new_schema = category.generate_schema(UserABC(username="test"), language_manager)
    assert new_schema == category_schema_data
