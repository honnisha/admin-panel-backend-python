from fastapi import FastAPI

from admin_panel.api.routers import admin_panel_router
from admin_panel.schema import AdminSchema


def generate_app(schema: AdminSchema) -> FastAPI:
    app = FastAPI(title="Admin Panel API")

    if not isinstance(schema, AdminSchema):
        raise TypeError('schema must be instance of admin_panel.schema.AdminSchema')

    app.state.schema = schema
    app.include_router(admin_panel_router)
    return app
