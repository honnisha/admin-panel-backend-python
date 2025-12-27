import abc
from typing import Any, ClassVar, List, Tuple

from pydantic.dataclasses import dataclass

from admin_panel.exceptions import FieldError
from admin_panel.schema.category import FieldSchemaData
from admin_panel.translations import LanguageManager, TranslateText
from admin_panel.utils import DeserializeAction


@dataclass
class TableField(abc.ABC, FieldSchemaData):
    _type: ClassVar[str]

    label: str | TranslateText | None = None
    help_text: str | TranslateText | None = None

    def generate_schema(self, user, field_slug, language_manager: LanguageManager) -> FieldSchemaData:
        schema = FieldSchemaData(
            type=self._type,
            label=language_manager.get_text(self.label) or field_slug,
            help_text=language_manager.get_text(self.help_text),
            header=self.header,
            read_only=self.read_only,
            default=self.default,
            required=self.required,
        )

        return schema

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        return value

    async def deserialize(self, value, action: DeserializeAction, extra: dict, *args, **kwargs) -> Any:
        if self.required and value is None:
            raise FieldError('Field is required', 'field_required')

        return value

    async def autocomplete(self, model, data, user):
        raise NotImplementedError()

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def set_deserialized_value(self, result: dict, field_slug, deserialized_value, action, extra):
        result[field_slug] = deserialized_value


@dataclass
class IntegerField(TableField):
    _type = 'integer'

    max_value: int | None = None
    min_value: int | None = None

    inputmode: str | None = None
    precision: int | None = None
    scale: int | None = None

    def generate_schema(self, user, field_slug, language_manager: LanguageManager) -> FieldSchemaData:
        schema = super().generate_schema(user, field_slug, language_manager)

        schema.choices = self.choices

        if self.max_value is not None:
            schema.max_value = self.max_value

        if self.min_value is not None:
            schema.min_value = self.min_value

        schema.inputmode = self.inputmode
        schema.precision = self.precision
        schema.scale = self.scale

        return schema


@dataclass
class StringField(TableField):
    _type = 'string'

    min_length: int | None = None
    max_length: int | None = None

    choices: List[Tuple[str, str]] | None = None

    def generate_schema(self, user, field_slug, language_manager: LanguageManager) -> FieldSchemaData:
        schema = super().generate_schema(user, field_slug, language_manager)

        schema.choices = self.choices

        if self.min_length is not None:
            schema.min_length = self.min_length

        if self.max_length is not None:
            schema.max_length = self.max_length

        return schema


@dataclass
class BooleanField(TableField):
    _type = 'boolean'


@dataclass
class DateTimeField(TableField):
    _type = 'datetime'

    format: str = '%Y-%m-%dT%H:%M:%S.%fZ'
    range: bool | None = None

    def generate_schema(self, user, field_slug, language_manager: LanguageManager) -> FieldSchemaData:
        schema = super().generate_schema(user, field_slug, language_manager)

        schema.range = self.range

        return schema

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        if value:
            return value.strftime(self.format)
        return value


@dataclass
class JSONField(TableField):
    _type = 'json'


@dataclass
class ArrayField(TableField):
    _type = 'array'

    array_type: str | None

    def generate_schema(self, user, field_slug, language_manager: LanguageManager) -> FieldSchemaData:
        schema = super().generate_schema(user, field_slug, language_manager)

        schema.array_type = self.array_type

        return schema


@dataclass
class FileField(TableField):
    _type = 'file'


@dataclass
class ImageField(TableField):
    _type = 'image'

    preview_max_height: int = 100
    preview_max_width: int = 100

    def generate_schema(self, user, field_slug, language_manager: LanguageManager) -> FieldSchemaData:
        schema = super().generate_schema(user, field_slug, language_manager)

        if self.preview_max_height is not None:
            schema.preview_max_height = self.preview_max_height

        if self.preview_max_width is not None:
            schema.preview_max_width = self.preview_max_width

        return schema

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        return {'url': value}


@dataclass
class ChoiceField(TableField):
    _type = 'choice'

    # https://vuetifyjs.com/en/styles/colors/#classes
    tag_colors: dict | None = None

    # https://vuetifyjs.com/en/components/chips/#color-and-variants
    variant: str = 'elevated'
    size: str = 'default'

    def generate_schema(self, user, field_slug, language_manager: LanguageManager) -> FieldSchemaData:
        schema = super().generate_schema(user, field_slug, language_manager)

        schema.choices = self.choices

        schema.tag_colors = self.tag_colors
        schema.size = self.size
        schema.variant = self.variant

        return schema

    async def serialize(self, value, extra: dict, *args, **kwargs) -> Any:
        return {'value': value, 'title': value.capitalize() if value else value}
