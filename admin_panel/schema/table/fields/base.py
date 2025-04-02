import abc
from dataclasses import dataclass
from typing import Any, List, Tuple

from admin_panel.api.api_exception import FieldError
from admin_panel.schema.table.fields.deserialize_action_types import DeserializeAction


@dataclass
class TableField(abc.ABC):
    _type: str

    label: str | None = None
    help_text: str | None = None
    read_only: bool = False
    default: Any | None = None
    required: bool = False

    # Table header parameters
    header: dict | None = None

    def generate_schema(self, user, field_slug) -> dict:
        schema = {}
        schema['type'] = self._type

        schema['label'] = self.label or field_slug
        schema['help_text'] = self.help_text
        schema['header'] = self.header
        schema['read_only'] = self.read_only
        schema['default'] = self.default
        schema['required'] = self.required

        return schema

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        return value

    async def deserialize(self, value, action: DeserializeAction, extra: dict, *args, **kwargs) -> Any:
        if self.required and value is None:
            raise FieldError('Field is required', 'field_required')

        return value

    async def autocomplete(self, model, data):
        raise NotImplementedError()

    # pylint: disable=too-many-arguments
    def set_deserialized_value(self, result: dict, field_slug, deserialized_value, action, extra):
        result[field_slug] = deserialized_value


@dataclass
class IntegerField(TableField):
    _type: str = 'integer'

    max_value: int | None = None
    min_value: int | None = None

    choices: List[Tuple[str, int]] | None = None

    def generate_schema(self, user, field_slug) -> dict:
        schema = super().generate_schema(user, field_slug)

        schema['choices'] = self.choices

        if self.max_value is not None:
            schema['max_value'] = self.max_value

        if self.min_value is not None:
            schema['min_value'] = self.min_value

        return schema


@dataclass
class StringField(TableField):
    _type: str = 'string'

    min_length: int | None = None
    max_length: int | None = None

    choices: List[Tuple[str, str]] | None = None

    def generate_schema(self, user, field_slug) -> dict:
        schema = super().generate_schema(user, field_slug)

        schema['choices'] = self.choices

        if self.min_length is not None:
            schema['min_length'] = self.min_length

        if self.max_length is not None:
            schema['max_length'] = self.max_length

        return schema


@dataclass
class BooleanField(TableField):
    _type: str = 'boolean'


@dataclass
class DateTimeField(TableField):
    _type: str = 'datetime'

    format: str = '%Y-%m-%dT%H:%M:%S.%fZ'

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        if value:
            return value.strftime(self.format)
        return value


@dataclass
class DateTimeRangeField(TableField):
    _type: str = 'datetime_range'

    format: str = '%Y-%m-%dT%H:%M:%S.%fZ'

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        if value:
            return value.strftime(self.format)
        return value


@dataclass
class JSONField(TableField):
    _type: str = 'json'
