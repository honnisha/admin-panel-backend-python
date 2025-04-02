from typing import Dict

from admin_panel.api.api_exception import AdminAPIException, APIError, FieldError
from admin_panel.schema.table.fields.base import TableField
from admin_panel.schema.table.fields.deserialize_action_types import DeserializeAction
from admin_panel.schema.table.fields.function_field import FunctionField


class DeserializeError(Exception):
    pass


class FieldsSchema:
    _fields = None
    _fields_list = None

    def __init__(self):
        if not self._fields:
            self._fields = []
            for attribute_name in dir(self):
                attribute = getattr(self, attribute_name)
                if issubclass(attribute.__class__, TableField):
                    self._fields.append(attribute_name)

        # Generation FunctionField
        for attribute_name in dir(self):
            attribute = getattr(self, attribute_name)
            if getattr(attribute, '__function_field__', False):
                field = FunctionField(fn=attribute, **attribute.__kwargs__)
                field.read_only = True
                setattr(self, attribute.__name__, field)

    def _iter_fields(self):
        for attribute_name in self._fields:
            attribute = getattr(self, attribute_name, None)

            if not attribute:
                raise AttributeError(f'Field "{attribute_name}" not found or None in {self.__class__}')

            if not issubclass(attribute.__class__, TableField):
                raise AttributeError(f'Field {attribute_name} of {self.__class__}  is not instance of TableField')

            yield (attribute_name, attribute)

    def get_field(self, field_slug) -> TableField | None:
        return self.get_fields().get(field_slug)

    def get_fields(self) -> Dict[str, TableField]:
        assert len(self._fields) > 0, f'Schema {self.__class__} fields is empty'

        if self._fields_list is None:
            self._fields_list = {i[0]: i[1] for i in self._iter_fields()}

        return self._fields_list

    def generate_schema(self, user) -> dict:
        fields_schema = {}
        fields_schema['fields'] = {
            field_slug: field.generate_schema(user, field_slug)
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
