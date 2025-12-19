from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from admin_panel.auth import AdminAuthentication, AuthData, AuthResult
from admin_panel.exceptions import AdminAPIException, APIError

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    path='/login/',
    responses={401: {"model": APIError}},
)
async def login(request: Request, auth_data: AuthData) -> AuthResult:
    auth: AdminAuthentication = request.app.state.auth
    try:
        result: AuthResult = await auth.login(auth_data)
    except AdminAPIException as e:
        return JSONResponse(e.get_error().model_dump(mode='json'), status_code=e.status_code)

    return JSONResponse(content=result.dict())
