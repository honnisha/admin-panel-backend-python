from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from admin_panel.exceptions import AdminAPIException
from admin_panel.auth import AdminAuthentication
from admin_panel.schema import AdminSchema, AdminSchemaData

router = APIRouter(prefix="/schema", tags=["schema"])


@router.get(path='/')
async def schema_handler(request: Request) -> AdminSchemaData:
    schema: AdminSchema = request.app.state.schema

    auth: AdminAuthentication = request.app.state.auth
    try:
        user = await auth.authenticate(request.headers)
    except AdminAPIException as e:
        return JSONResponse(e.get_error().model_dump(mode='json'), status_code=e.status_code)

    language_slug = request.headers.get('Accept-Language')
    admin_schema = schema.generate_schema(user, language_slug)
    return admin_schema
