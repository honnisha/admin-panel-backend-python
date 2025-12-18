import asyncio
from typing import ClassVar, Dict, List

from pydantic.dataclasses import dataclass

from admin_panel.auth import UserABC
from admin_panel.exceptions import AdminAPIException, APIError, FieldError
from admin_panel.schema.table.fields.base import TableField
from admin_panel.schema.table.fields.function_field import FunctionField
from admin_panel.translations import LanguageManager
from admin_panel.utils import DeserializeAction


class DeserializeError(Exception):
    pass


@dataclass
class FieldsSchema:
    # Список полей
    fields: ClassVar[List[str] | None] = None

    # Для передачи параметра read_only = True внутрь поля
    readonly_fields: ClassVar[List | None] = None

    _fields_list: List | None = None

    # pylint: disable=too-many-branches
    def __post_init__(self):
        # Autogenerate fields
        if self.fields is None:
            self.fields = []
            for attribute_name in dir(self):
                if '__' in attribute_name:
                    continue

                attribute = getattr(self, attribute_name)
                if issubclass(attribute.__class__, TableField):
                    self.fields.append(attribute_name)

        if not self.fields:
            msg = f'Schema {type(self).__name__}.fields is empty'
            raise AttributeError(msg)

        # Generation FunctionField
        for attribute_name in dir(self):
            if '__' in attribute_name:
                continue

            attribute = getattr(self, attribute_name)
            if getattr(attribute, '__function_field__', False):
                field = FunctionField(fn=attribute, **attribute.__kwargs__)
                field.read_only = True
                setattr(self, attribute.__name__, field)

        # Check for fields not listed in self.fields
        for attribute_name in dir(self):
            if '__' in attribute_name:
                continue

            attribute = getattr(self, attribute_name)
            if issubclass(attribute.__class__, TableField) and attribute_name not in self.fields:
                msg = f'Schema {type(self).__name__} attribute "{attribute_name}" {type(attribute).__name__} presented, but not listed inside fields list: {self.fields}'
                raise AttributeError(msg)

        if self.readonly_fields:
            for field_slug in self.readonly_fields:
                field = self.get_field(field_slug)
                if not field:
                    msg = f'Field "{field_slug}" from readonly_fields is not found'
                    raise AttributeError(msg)

                field.read_only = True

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
        if self._fields_list is None:
            self._fields_list = {i[0]: i[1] for i in self._iter_fields()}

        return self._fields_list

    def generate_schema(self, user: UserABC, language_manager: LanguageManager) -> dict:
        fields_schema = {}
        fields_schema['fields'] = {
            field_slug: field.generate_schema(user, field_slug, language_manager)
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

                validate_method = getattr(self, f'validate_{field_slug}', None)
                if callable(validate_method):
                    if not asyncio.iscoroutinefunction(validate_method):
                        msg = f'Validate method {type(self).__name__}.{field_slug} must be async'
                        raise AttributeError(msg)
                    deserialized_value = await validate_method(value)

                field.set_deserialized_value(result, field_slug, deserialized_value, action, extra)
            except FieldError as e:
                errors[field_slug] = e

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
