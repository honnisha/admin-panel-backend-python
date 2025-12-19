import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from admin_panel import generate_app, schema
from admin_panel.auth import AdminAuthentication, AuthData, AuthResult, UserABC, UserResult
from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.translations import LanguageManager
from admin_panel.translations import TranslateText as _
from example.phrases import LANGUAGES_PHRASES
from example.sections.graphs import GraphsExample
from example.sections.payments import PaymentsAdmin


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


logging.config.dictConfig(LogConfig().model_dump())


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
    use_scalar=True,
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
