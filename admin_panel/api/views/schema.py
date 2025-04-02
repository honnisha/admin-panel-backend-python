from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from admin_panel.api.api_exception import AdminAPIException
from admin_panel.controllers import AdminAuthentication

router = APIRouter(prefix="/schema", tags=["schema"])


@router.get(path='/')
async def schema(request: Request):
    auth: AdminAuthentication = request.app.state.auth
    try:
        user = await auth.authenticate(request.headers)
    except AdminAPIException as e:
        return JSONResponse(e.get_error(), status_code=e.status_code)

    return JSONResponse(content=request.app.state.schema.generate_schema(user))
