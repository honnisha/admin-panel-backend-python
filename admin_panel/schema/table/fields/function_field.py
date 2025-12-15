import asyncio
import functools
import logging
from typing import Any

from pydantic.dataclasses import dataclass

from admin_panel.exceptions import AdminAPIException, APIError
from admin_panel.schema.table.fields.base import TableField

logger = logging.getLogger('admin_panel')


def function_field(**kwargs):
    '''
    The same as decaring:
    field = FunctionField(fn=attribute)

    but available directly and converted after to the FunctionField
    '''
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

    fn: Any = None

    def __post_init__(self):
        if not asyncio.iscoroutinefunction(self.fn):
            msg = f'{type(self).__name__}.fn {self.fn} must be coroutine function'
            raise AttributeError(msg)

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        try:
            return await self.fn(**extra)
        except Exception as e:
            logger.exception(
                'Function field %s label=%s error from function="%s": %s',
                type(self).__name__,
                self.label,
                self.fn,
                e,
            )
            raise AdminAPIException(
                APIError(message=f'Error: {e}', code='function_field_error'), status_code=400,
            ) from e
