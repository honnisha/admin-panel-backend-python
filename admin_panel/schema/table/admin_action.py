from dataclasses import asdict, dataclass
import functools
from typing import Any, List, Optional

from pydantic import BaseModel

from admin_panel.schema.table.fields_schema import FieldsSchema
from admin_panel.schema.table.table_models import ListFilters


class ActionData(BaseModel):
    pks: List[Any]
    form_data: dict
    filters: ListFilters
    send_to_all: bool


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


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
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
