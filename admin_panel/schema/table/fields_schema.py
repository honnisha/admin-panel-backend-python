from typing import Dict, List

from pydantic.dataclasses import dataclass

from admin_panel.api.api_exception import AdminAPIException, APIError, FieldError
from admin_panel.schema.base import UserABC
from admin_panel.schema.table.fields.base import TableField
from admin_panel.schema.table.fields.deserialize_action_types import DeserializeAction
from admin_panel.schema.table.fields.function_field import FunctionField
from admin_panel.utils import LanguageManager


class DeserializeError(Exception):
    pass


@dataclass
class FieldsSchema:
    fields: List | None = None

    fields_list: List | None = None
    readonly_fields: List | None = None

    def __post_init__(self):
        if not self.fields:
            self.fields = []
            for attribute_name in dir(self):
                if '__' in attribute_name:
                    continue

                attribute = getattr(self, attribute_name)
                if issubclass(attribute.__class__, TableField):
                    self.fields.append(attribute_name)

        # Generation FunctionField
        for attribute_name in dir(self):
            if '__' in attribute_name:
                continue

            attribute = getattr(self, attribute_name)
            if getattr(attribute, '__function_field__', False):
                field = FunctionField(fn=attribute, **attribute.__kwargs__)
                field.read_only = True
                setattr(self, attribute.__name__, field)

    def _iter_fields(self):
        for attribute_name in self.fields:
            attribute = getattr(self, attribute_name, None)

            if not attribute:
                msg = f'Field "{attribute_name}" not found or None in {self.__class__}'
                raise AttributeError(msg)

            if not issubclass(attribute.__class__, TableField):
                msg = f'Field {type(self).__name__}.{attribute_name} is not TableField issubclass: {attribute}'
                raise AttributeError(msg)

            yield (attribute_name, attribute)

    def get_field(self, field_slug) -> TableField | None:
        return self.get_fields().get(field_slug)

    def get_fields(self) -> Dict[str, TableField]:
        if not self.fields:
            msg = f'Schema {type(self).__name__}.fields is empty'
            raise AttributeError(msg)

        if self.fields_list is None:
            self.fields_list = {i[0]: i[1] for i in self._iter_fields()}

        return self.fields_list

    def generate_schema(self, user: UserABC, language: LanguageManager) -> dict:
        fields_schema = {}
        fields_schema['fields'] = {
            field_slug: field.generate_schema(user, field_slug, language)
            for field_slug, field in self.get_fields().items()
        }
        return fields_schema

    async def serialize(self, line_data: dict, extra: dict) -> dict:
        result = {}
        for field_slug, field in self.get_fields().items():
            value = line_data.get(field_slug)
            result[field_slug] = await field.serialize(value, extra)
        return result

    async def deserialize(self, data: dict, action: DeserializeAction, extra) -> dict:
        result = {}
        errors = {}
        for field_slug, field in self.get_fields().items():

            if field.read_only:
                continue

            value = data.get(field_slug)
            try:
                deserialized_value = await field.deserialize(value, action, extra)
                field.set_deserialized_value(result, field_slug, deserialized_value, action, extra)
            except FieldError as e:
                errors[field_slug] = e.get_error()

        if errors:
            raise AdminAPIException(
                APIError(
                    message='Validation error',
                    code='validation_error',
                    field_errors=errors,
                ),
                status_code=400,
            )
        return result
