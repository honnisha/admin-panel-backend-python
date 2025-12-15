# pylint: disable=wildcard-import, unused-wildcard-import, unused-import
# flake8: noqa: F405

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from admin_panel.api.routers import admin_panel_router
from admin_panel.auth import AdminAuthentication
from admin_panel.schema import AdminSchema

from .integrations import django, sqlalchemy


def generate_app(
        schema: AdminSchema,
        auth: AdminAuthentication,
        debug=False,
) -> FastAPI:
    app = FastAPI(title=schema.title, debug=debug)

    app.mount("/static", StaticFiles(directory="admin_panel/static"), name="static")

    if not isinstance(schema, AdminSchema):
        raise TypeError('schema must be instance of admin_panel.schema.AdminSchema')

    app.state.schema = schema
    app.state.auth = auth
    app.include_router(admin_panel_router)
    return app
