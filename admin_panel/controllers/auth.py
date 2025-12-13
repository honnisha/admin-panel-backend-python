import abc

from pydantic import BaseModel

from admin_panel.api.api_exception import AdminAPIException, APIError
from admin_panel.schema.base import UserABC


class AuthData(BaseModel):
    username: str
    password: str


class UserResult(BaseModel):
    username: str


class AuthResult(BaseModel):
    token: str
    user: UserResult


class AdminAuthentication(abc.ABC):
    async def login(self, data: AuthData) -> AuthResult:
        raise NotImplementedError()

    async def authenticate(self, headers: dict) -> UserABC:
        raise NotImplementedError()


class DjangoJWTAdminAuthentication(AdminAuthentication):
    secret: str

    def __init__(self, secret: str):
        self.secret = secret

    async def login(self, data: AuthData) -> AuthResult:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = await User.objects.filter(username=data.username).afirst()
        if not user:
            raise AdminAPIException(APIError(message='User not found', code='user_not_found'), status_code=401)

        if not user.is_staff:
            raise AdminAPIException(APIError(message='User is not an admin', code='not_an_admin'), status_code=401)

        import jwt
        token = jwt.encode({"user_pk": user.pk}, self.secret, algorithm="HS256")
        return AuthResult(token=token, user=UserResult(username=user.username))


    async def authenticate(self, headers: dict) -> UserABC:
        token = headers.get('Authorization')
        if not token:
            raise AdminAPIException(APIError(message='Token is not presented'), status_code=401)

        token = token.replace('Token ', '')
        import jwt
        try:
            auth_payload = jwt.decode(token, self.secret, algorithms=["HS256"])
        except jwt.exceptions.DecodeError as e:
            raise AdminAPIException(APIError(message='Token decoding error', code='token_error'), status_code=401)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = await User.objects.filter(pk=auth_payload.get('user_pk'), is_staff=True).afirst()
        if not user:
            raise AdminAPIException(APIError(message='User not found', code='user_not_found'), status_code=401)

        return user
