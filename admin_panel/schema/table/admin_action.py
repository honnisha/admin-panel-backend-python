import functools
from typing import Any, List, Optional

from pydantic import BaseModel, validate_arguments
from pydantic.dataclasses import dataclass

from admin_panel.schema.table.fields_schema import FieldsSchema
from admin_panel.schema.table.table_models import ListFilters
from admin_panel.utils import DataclassBase, TranslateText


class ActionData(BaseModel):
    pks: List[Any]
    form_data: dict
    filters: ListFilters
    send_to_all: bool


@dataclass
class ActionMessage(DataclassBase):
    text: str | TranslateText
    type: str = 'success'
    position: str = 'top-center'


@dataclass
class ActionResult(DataclassBase):
    message: ActionMessage | None = None
    persistent_message: str | TranslateText | None = None


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
@validate_arguments
def admin_action(
    title: str | TranslateText,
    description: Optional[str | TranslateText] = None,
    confirmation_text: Optional[str | TranslateText] = None,

    # https://vuetifyjs.com/en/styles/colors/#material-colors
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
            'confirmation_text': confirmation_text,

            'icon': icon,
            'base_color': base_color,
            'variant': variant,

            'allow_empty_selection': allow_empty_selection,
            'form_schema': form_schema,
        }

        @functools.wraps(func)
        async def wrapped(*args):
            return await func(*args)

        return wrapped

    return wrapper
