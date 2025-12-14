from typing import Dict

from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from admin_panel.utils import DataclassBase


class FieldErrorModel(BaseModel):
    message: str
    code: str | None = None


class AdminAPIErrorModel(BaseModel):
    data: dict
    code: str | None
    field_errors: Dict[str, FieldErrorModel] | None = None


@dataclass
class APIError(DataclassBase):
    message: str | None = None
    code: str | None = None
    field_errors: dict | None = None


class FieldError(Exception):
    message = None
    code = None

    def __init__(self, message, code: str):
        self.message = message
        self.code = code

    def get_error(self):
        return {'message': self.message, 'code': self.code}


class AdminAPIException(Exception):
    data: APIError
    status_code: int
    error_code: str | None = None

    def __init__(self, data: APIError, status_code: int = 400):
        self.data = data
        self.status_code = status_code

    def __str__(self):
        return str(self.data)

    def get_error(self) -> dict:
        return self.data.model_dump(mode='json')
