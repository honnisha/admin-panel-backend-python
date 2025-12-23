import asyncio
import logging.config

from fastapi import FastAPI
from pydantic import BaseModel

from admin_panel import schema
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


LOGIN_GREETINGS_MESSAGE = '''
<div class="text-h6 mb-1">
  Demo mode
</div>
<div class="text-caption">
  Login: admin<br>
  Password: admin
</div>
'''


class FakeAdminAuthentication(AdminAuthentication):
    async def login(self, data: AuthData) -> AuthResult:
        await asyncio.sleep(1.0)

        if data.username != 'admin' or data.password != 'admin':
            raise AdminAPIException(APIError(code='user_not_found'), status_code=401)

        return AuthResult(token='test', user=UserResult(username='test_admin'))

    async def authenticate(self, headers: dict) -> UserABC:
        return UserABC(username='test_admin')


admin_schema = schema.AdminSchema(
    title=_('admin_title'),
    description=_('admin_description'),
    login_greetings_message=_('login_greetings_message'),

    auth=FakeAdminAuthentication(),
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

admin_app = admin_schema.generate_app(
    include_scalar=True, include_docs=True, include_redoc=True, debug=True,
)
app.mount('/admin', admin_app)
