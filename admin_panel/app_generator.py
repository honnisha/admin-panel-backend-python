from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from admin_panel.api.routers import admin_panel_router
from admin_panel.auth import AdminAuthentication
from admin_panel.docs import build_redoc_docs, build_scalar_docs
from admin_panel.schema import AdminSchema


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
def generate_app(
        schema: AdminSchema,
        auth: AdminAuthentication,
        use_scalar=False,
        debug=False,
) -> FastAPI:
    # pylint: disable=unused-variable
    language_manager = schema.get_language_manager(language_slug=None)

    app = FastAPI(
        title=language_manager.get_text(schema.title),
        description=language_manager.get_text(schema.description),
        debug=debug,
        docs_url='/docs',
        redoc_url=None,
    )

    app.mount("/static", StaticFiles(directory="admin_panel/static"), name="static")

    if not isinstance(schema, AdminSchema):
        raise TypeError('schema must be instance of admin_panel.schema.AdminSchema')

    app.state.schema = schema
    app.state.auth = auth

    if use_scalar:
        app.include_router(build_scalar_docs(app))

    app.include_router(build_redoc_docs(app, redoc_url='/redoc'))

    app.include_router(admin_panel_router)

    return app
