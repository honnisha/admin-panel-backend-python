import asyncio
from typing import Any, ClassVar, Dict, List

from pydantic_core import core_schema

from admin_panel.auth import UserABC
from admin_panel.exceptions import AdminAPIException, APIError, FieldError
from admin_panel.schema.category import FieldsSchemaData
from admin_panel.schema.table.fields.base import TableField
from admin_panel.schema.table.fields.function_field import FunctionField
from admin_panel.translations import LanguageManager
from admin_panel.utils import DeserializeAction


class DeserializeError(Exception):
    pass


class FieldsSchema:
    # Список полей
    fields: List[str] | None = None

    # Список колонок, которые будут отображаться в таблице
    list_display: List[str] | None = None

    # Для передачи параметра read_only = True внутрь поля
    readonly_fields: ClassVar[List | None] = None

    # Generated fields
    _fields_list: List | None = None

    def __init__(self, *args, list_display=None, readonly_fields=None, fields=None, **kwargs):
        if fields:
            self.fields = fields

        if list_display:
            self.list_display = list_display

        if readonly_fields:
            self.readonly_fields = readonly_fields

        # Fields from kwargs
        for k, v in kwargs.items():
            if issubclass(type(v), TableField):
                setattr(self, k, v)

        # Generation FunctionField
        for attribute_name in dir(self):
            if '__' in attribute_name:
                continue

            attribute = getattr(self, attribute_name)
            if getattr(attribute, '__function_field__', False):
                field = FunctionField(fn=attribute, **attribute.__kwargs__)
                field.read_only = True
                setattr(self, attribute.__name__, field)

        # Autogenerate fields
        if self.fields is None:
            self.fields = []
            for attribute_name in dir(self):
                if '__' in attribute_name:
                    continue

                attribute = getattr(self, attribute_name)
                if issubclass(type(attribute), TableField):
                    self.fields.append(attribute_name)

        self.post_init(*args, **kwargs)

    def post_init(self, *args, **kwargs):

        if not self.fields:
            msg = f'Schema {type(self).__name__}.fields is empty'
            raise AttributeError(msg)

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

        if self.list_display is None:
            self.list_display = self.fields

        for field_slug in self.list_display:
            if field_slug not in self.fields:
                msg = f'Field "{field_slug}" inside {type(self).__name__}.list_display, but not presented as field; available options: {self.fields}'
                raise AttributeError(msg)

    def _generate_fields(self):
        for attribute_name in self.fields:
            if not isinstance(attribute_name, str):
                msg = f'{type(self).__name__} field "{attribute_name}" must be string'
                raise AttributeError(msg)

            attribute = getattr(self, attribute_name, None)

            if not attribute:
                msg = f'Field slug "{attribute_name}" not found as attribute in {type(self).__name__}'
                raise AttributeError(msg)

            if not issubclass(attribute.__class__, TableField):
                msg = f'Field {type(self).__name__}.{attribute_name} is not TableField issubclass: {attribute}'
                raise AttributeError(msg)

            yield (attribute_name, attribute)

    def get_field(self, field_slug) -> TableField | None:
        return self.get_fields().get(field_slug)

    def get_fields(self) -> Dict[str, TableField]:
        if self._fields_list is None:
            self._fields_list = {i[0]: i[1] for i in self._generate_fields()}

        return self._fields_list

    def generate_schema(self, user: UserABC, language_manager: LanguageManager) -> FieldsSchemaData:
        fields_schema = FieldsSchemaData(
            list_display=self.list_display,
        )
        fields_schema.fields = {
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

            # Skip update if fields is not presented in data
            if action == DeserializeAction.UPDATE and field_slug not in data:
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

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        def validate(v: Any) -> "FieldsSchema":
            if isinstance(v, cls):
                return v
            raise TypeError(f"Expected {cls.__name__} instance")

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: repr(v),
                info_arg=False,
                return_schema=core_schema.str_schema(),
            ),
        )
