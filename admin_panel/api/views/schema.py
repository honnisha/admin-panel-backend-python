from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from admin_panel.api.api_exception import AdminAPIException
from admin_panel.controllers import AdminAuthentication
from admin_panel.schema.base import AdminSchema

router = APIRouter(prefix="/schema", tags=["schema"])


@router.get(path='/')
async def schema_handler(request: Request):
    schema: AdminSchema = request.app.state.schema

    auth: AdminAuthentication = request.app.state.auth
    try:
        user = await auth.authenticate(request.headers)
    except AdminAPIException as e:
        return JSONResponse(e.get_error(), status_code=e.status_code)

    language_slug = request.headers.get('Accept-Language')
    return JSONResponse(content=schema.generate_schema(user, language_slug))
