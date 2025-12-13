import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from admin_panel import generate_app, schema
from admin_panel.controllers import DjangoJWTAdminAuthentication
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


admin_schema = schema.AdminSchema(groups=[
    schema.Group(
        slug='payments',
        title='Платежи',
        icon='mdi-credit-card-outline',
        categories=[
            PaymentsAdmin(),
        ]
    ),
    schema.Group(
        slug='statistics',
        title='Статистика',
        icon='mdi-finance',
        categories=[
            GraphsExample(),
        ]
    ),
])

app = FastAPI(debug=True)

admin_app = generate_app(
    admin_schema,
    auth=DjangoJWTAdminAuthentication(secret='test'),
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
