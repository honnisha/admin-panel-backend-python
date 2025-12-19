from typing import Any, Dict, List

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

from admin_panel.utils import DataclassBase


@dataclass
class TableListResult(DataclassBase):
    data: List[dict]
    total_count: int


class ListFilters(BaseModel):
    search: str | None = None
    filters: Dict[str, Any] = Field(default_factory=dict)


class AutocompleteData(BaseModel):
    search_string: str
    field_slug: str
    is_filter: bool
    form_data: dict
    existed_choices: List[Any] = Field(default_factory=list)
    action_name: str | None = None
    limit: int = 25


class Record(BaseModel):
    key: Any
    title: str


class AutocompleteResult(BaseModel):
    results: List[Record]


class ListData(BaseModel):
    page: int = 1
    limit: int = 25
    filters: ListFilters
    search: str | None = None
    ordering: str | None = None


class CreateResult(BaseModel):
    pk: Any


class UpdateResult(BaseModel):
    pk: Any
