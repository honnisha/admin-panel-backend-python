from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from admin_panel.api.api_exception import AdminAPIErrorModel, AdminAPIException
from admin_panel.controllers import AdminAuthentication, AuthData, AuthResult

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    path='/login/',
    responses={401: {"model": AdminAPIErrorModel}},
)
async def login(request: Request, auth_data: AuthData) -> AuthResult:
    auth: AdminAuthentication = request.app.state.auth
    try:
        result: AuthResult = await auth.login(auth_data)
    except AdminAPIException as e:
        return JSONResponse(e.get_error(), status_code=e.status_code)

    return JSONResponse(content=result.dict())
