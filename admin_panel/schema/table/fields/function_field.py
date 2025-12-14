import asyncio
import functools
from typing import Annotated, Any

from pydantic import AfterValidator
from pydantic.dataclasses import dataclass

from admin_panel.schema.table.fields.base import TableField


def function_field(**kwargs):
    def wrapper(func):
        func.__function_field__ = True

        field_type = kwargs.pop('type', None)
        if field_type:
            # pylint: disable=protected-access
            kwargs['_type'] = field_type._type

        func.__kwargs__ = kwargs

        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapped

    return wrapper


@dataclass
class FunctionField(TableField):
    _type: str = 'function_field'
    read_only = True

    fn: Annotated[Any | None, AfterValidator(asyncio.iscoroutinefunction)] = None

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        return await self.fn(**extra)
