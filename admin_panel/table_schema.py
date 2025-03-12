import abc
import asyncio
import functools
from dataclasses import asdict, dataclass
from typing import Any, Dict, Generator, List, Optional, Tuple

from fastapi import HTTPException
from pydantic import BaseModel

from admin_panel.schema import Category


@dataclass
class TableField(abc.ABC):
    _slug: str

    label: str | None = None
    help_text: str | None = None

    header: dict | None = None

    def generate_schema(self) -> dict:
        result = asdict(self)
        result['label'] = self.label or self._slug
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class IntegerField(TableField):
    _slug: str = 'integer'

    max_value: int | None = None
    min_value: int | None = None


class FieldsSchema:

    def iter_fields(self) -> Generator[Tuple[str, TableField], None, None]:
        for attribute_name in dir(self):
            attribute = getattr(self, attribute_name)
            if issubclass(attribute.__class__, TableField):
                yield (attribute_name, attribute)

    def generate_schema(self) -> dict:
        return {field_name: field.generate_schema() for field_name, field in self.iter_fields()}


@dataclass
class TableListResult:
    data: dict
    total_count: int

    def asdict(self):
        return asdict(self)


def admin_action(
    title: str,
    description: Optional[str] = None,
    short_description: Optional[str] = None,
    confirmation_text: Optional[str] = None,

    base_color: Optional[str] = None,

    # https://pictogrammers.com/library/mdi/
    icon: Optional[str] = None,

    # elevated, flat, tonal, outlined, text, and plain.
    variant: Optional[str] = None,

    allow_empty_selection: bool = False,
    form_schema: Optional[FieldsSchema] = None,
):
    def wrapper(func):
        func.__action__ = True

        func.action_info = {
            'title': title,
            'description': description,
            'short_description': short_description,
            'confirmation_text': confirmation_text,

            'icon': icon,
            'base_color': base_color,
            'variant': variant,

            'allow_empty_selection': allow_empty_selection,
            'form_schema': form_schema.generate_schema() if form_schema else None,
        }

        @functools.wraps(func)
        async def wrapped(*args):
            return await func(*args)

        return wrapped

    return wrapper


class ListFilters(BaseModel):
    search: str | None
    filters: Dict[str, Any]


class ActionData(BaseModel):
    pks: List[Any]
    form_data: dict
    filters: ListFilters
    send_to_all: bool


class ListData(BaseModel):
    page: int
    limit: int
    filters: ListFilters
    search: str | None = None
    ordering: str | None = None


@dataclass
class ActionMessage:
    text: str
    type: str = 'success'
    position: str = 'top-center'


@dataclass
class ActionResult:
    message: ActionMessage | None = None
    persistent_message: str | None = None

    def asdict(self):
        return asdict(self)


class CategoryTable(Category):
    type_slug: str = 'table'

    table_schema: FieldsSchema
    table_filters: FieldsSchema | None = None

    ordering_fields: List[str] = []

    pk_name: str = 'id'

    @property
    def has_retrieve(self):
        fn = getattr(self, 'retrieve', None)
        return asyncio.iscoroutinefunction(fn)

    @property
    def has_create(self):
        fn = getattr(self, 'create', None)
        return asyncio.iscoroutinefunction(fn)

    @property
    def has_update(self):
        fn = getattr(self, 'update', None)
        return asyncio.iscoroutinefunction(fn)

    def generate_schema(self) -> dict:
        schema = super().generate_schema()
        table = {}

        table['table_schema'] = self.table_schema.generate_schema()
        table['ordering_fields'] = self.ordering_fields

        table['pk_name'] = self.pk_name
        table['can_retrieve'] = self.has_retrieve

        table['can_create'] = self.has_create
        table['can_update'] = self.has_update

        table['table_filters'] = None
        if self.table_filters:
            table['table_filters'] = self.table_filters.generate_schema()

        actions = {}
        for attribute_name in dir(self):
            attribute = getattr(self, attribute_name)
            if asyncio.iscoroutinefunction(attribute) and getattr(attribute, '__action__', False):
                action = attribute.action_info
                actions[attribute_name] = action

        table['actions'] = actions

        schema['table_info'] = table
        return schema

    async def _perform_action(self, action: str, action_data: ActionData) -> dict:
        attribute = getattr(self, action)
        if not asyncio.iscoroutinefunction(attribute) or not getattr(attribute, '__action__', False):
            raise HTTPException(status_code=404, detail=f"Action \"{action}\" is not found")

        try:
            result: ActionResult = await attribute(action_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Action \"{action}\" error: {e}") from e

        return result

    # pylint: disable=too-many-arguments
    @abc.abstractmethod
    async def get_list(self, list_data: ListData) -> TableListResult:
        raise NotImplementedError()

#     async def retrieve(self, pk: Any) -> Optional[dict]:
#        raise NotImplementedError()

#    async def create(self, data: dict):
#        raise NotImplementedError()

#    async def update(self, pk: Any, data: dict):
#        raise NotImplementedError()
