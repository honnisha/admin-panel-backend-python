from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.auth import AdminAuthentication, AuthData, AuthResult, UserABC, UserResult


class DjangoJWTAdminAuthentication(AdminAuthentication):
    secret: str

    def __init__(self, secret: str):
        self.secret = secret

    async def login(self, data: AuthData) -> AuthResult:
        import jwt  # pylint: disable=import-outside-toplevel
        from django.contrib.auth import get_user_model  # pylint: disable=import-outside-toplevel

        User = get_user_model()
        user = await User.objects.filter(username=data.username).afirst()
        if not user:
            raise AdminAPIException(APIError(message='User not found', code='user_not_found'), status_code=401)

        if not user.is_staff:
            raise AdminAPIException(APIError(message='User is not an admin', code='not_an_admin'), status_code=401)

        token = jwt.encode({"user_pk": user.pk}, self.secret, algorithm="HS256")
        return AuthResult(token=token, user=UserResult(username=user.username))

    async def authenticate(self, headers: dict) -> UserABC:
        import jwt  # pylint: disable=import-outside-toplevel
        from django.contrib.auth import get_user_model  # pylint: disable=import-outside-toplevel

        token = headers.get('Authorization')
        if not token:
            raise AdminAPIException(APIError(message='Token is not presented'), status_code=401)

        token = token.replace('Token ', '')
        try:
            auth_payload = jwt.decode(token, self.secret, algorithms=["HS256"])
        except jwt.exceptions.DecodeError as e:
            raise AdminAPIException(
                APIError(message='Token decoding error', code='token_error'), status_code=401
            ) from e

        User = get_user_model()
        user = await User.objects.filter(pk=auth_payload.get('user_pk'), is_staff=True).afirst()
        if not user:
            raise AdminAPIException(APIError(message='User not found', code='user_not_found'), status_code=401)

        return user
