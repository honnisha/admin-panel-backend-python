import abc

from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from admin_panel.utils import DataclassBase


@dataclass
class UserABC(DataclassBase, abc.ABC):
    username: str


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
