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
from example.sections.currency import CurrencyAdmin
from example.sections.graphs import GraphsExample
from example.sections.merchant import MerchantAdmin
from example.sections.payments import PaymentsAdmin
from example.sections.terminal import TerminalAdmin
from example.sections.users import UserAdmin
from example.sqlite import async_sessionmaker_, lifespan


class ExtraFormatter(logging.Formatter):
    _standard_attrs = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
        'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
        'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
        'thread', 'threadName', 'processName', 'process',
        'message', 'asctime'
    }

    def format(self, record: logging.LogRecord) -> str:
        extra = {
            k: v for k, v in record.__dict__.items()
            if k not in self._standard_attrs
        }

        record.extra = extra
        return super().format(record)


class LogConfig(BaseModel):
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": ExtraFormatter,
            "fmt": "%(levelname)s %(asctime)s: %(message)s | extra: %(extra)s",
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
            slug='users',
            title=_('users'),
            icon='mdi-account',
            categories=[
                UserAdmin(db_async_session=async_sessionmaker_),
            ]
        ),
        schema.Group(
            slug='merchants',
            title=_('merchants'),
            icon='mdi-folder-account-outline',
            categories=[
                MerchantAdmin(db_async_session=async_sessionmaker_),
                TerminalAdmin(db_async_session=async_sessionmaker_),
            ]
        ),
        schema.Group(
            slug='currencies',
            title=_('currencies'),
            icon='mdi-cash-multiple',
            categories=[
                CurrencyAdmin(db_async_session=async_sessionmaker_),
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


app = FastAPI(debug=True, lifespan=lifespan)

admin_app = admin_schema.generate_app(
    include_scalar=True, include_docs=True, include_redoc=True, debug=True,
)
app.mount('/admin', admin_app)
