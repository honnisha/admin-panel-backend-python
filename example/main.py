import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from admin_panel import generate_app, schema
from admin_panel.api.api_exception import AdminAPIException, APIError
from admin_panel.controllers.auth import AdminAuthentication, AuthData, AuthResult, UserResult
from admin_panel.schema.base import UserABC
from admin_panel.utils import LanguageManager
from admin_panel.utils import TranslateText as _
from example.graphs import GraphsExample
from example.payments import PaymentsAdmin


class LogConfig(BaseModel):
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },

    }
    loggers: dict = {
        "admin_panel": {"handlers": ["default"], "level": "INFO"},
    }


logging.config.dictConfig(LogConfig().dict())

LANGUAGES_PHRASES = {
    'ru': {
        'admin_title': 'Admin Panel Демо',
        'created_at': 'Время создания',
        'graphs_example': 'Пример графиков',
        'amount': 'Сумма',
        'registry_checked': 'Реестр проверен',
        'registry_info_checked': 'Информация по реестру провайдера',
        'payments': 'Платежи',
        'statistics': 'Статистика',
        'image': 'Изображение',
        'delete': 'Удалить',
        'delete_confirmation_text': 'Вы уверены, что хотите удалить данные записи?\nДанное действие нельзя отменить.',
        'payments_search_fields': 'Доступные поля для поиска: id',
        'create_payment': 'Создать платеж',
        'create_payment_description': 'Создать платеж и отправить его на обработку в платежную систему.',
        'payment_create_result': 'Платеж успешно создан. Данные платежа:<br><br>gateway_id=%(gateway_id)s<br><br>redirect_url: <a href="%(redirect_url)s" target="_blank"/>%(redirect_url)s</a>',
        'description': 'Описание',
        'status': 'Статус',
        'endpoint': 'Эндпоинт',
    },
    'en': {
        'admin_title': 'Admin Panel Demo',
        'created_at': 'Created time',
        'graphs_example': 'Graphs example',
        'amount': 'Amount',
        'registry_checked': 'Registry checked',
        'registry_info_checked': 'Registry info checked',
        'payments': 'Payments',
        'statistics': 'Statistics',
        'image': 'Image',
        'delete': 'Delete',
        'delete_confirmation_text': 'Are you sure you want to delete those records?\nThis action cannot be undone.',
        'payments_search_fields': 'Search fields: id',
        'create_payment': 'Create payment',
        'create_payment_description': 'Create a payment and send it to the payment system for processing.',
        'payment_create_result': 'The payment was created successfully. Payment details:<br><br>gateway_id=%(gateway_id)s<br><br>redirect_url: <a href="%(redirect_url)s" target="_blank"/>%(redirect_url)s</a>',
        'description': 'Description',
        'status': 'Status',
        'endpoint': 'Endpoint',
    },
}


class CustomLanguageManager(LanguageManager):
    languages = {
        'ru': 'Russian',
        'en': 'English',
        'test': 'Test',
    }
    languages_phrases = LANGUAGES_PHRASES


admin_schema = schema.AdminSchema(
    title=_('admin_title'),
    language_manager_class=CustomLanguageManager,
    groups=[
        schema.Group(
            slug='payments',
            title=_('payments'),
            icon='mdi-cash-multiple',
            categories=[
                PaymentsAdmin(),
            ]
        ),
        schema.Group(
            slug='statistics',
            title=_('statistics'),
            icon='mdi-finance',
            categories=[
                GraphsExample(),
            ]
        ),
    ],
)

app = FastAPI(debug=True)


class FakeAdminAuthentication(AdminAuthentication):
    async def login(self, data: AuthData) -> AuthResult:
        if data.username != 'admin' and data.password != 'admin':
            raise AdminAPIException(APIError(message='User not found', code='user_not_found'), status_code=401)

        return AuthResult(token='test', user=UserResult(username='test_admin'))

    async def authenticate(self, headers: dict) -> UserABC:
        return UserABC(username='test_admin')


admin_app = generate_app(
    admin_schema,
    auth=FakeAdminAuthentication(),
    debug=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount('/admin', admin_app)
