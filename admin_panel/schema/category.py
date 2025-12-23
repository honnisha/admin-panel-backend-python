import abc
from typing import Any, ClassVar, Dict, List

from pydantic import Field
from pydantic.dataclasses import dataclass

from admin_panel.auth import UserABC
from admin_panel.translations import LanguageManager, TranslateText
from admin_panel.utils import DataclassBase


# pylint: disable=too-many-instance-attributes
@dataclass
class FieldSchemaData(DataclassBase):
    type: str = None

    label: str | None = None
    help_text: str | None = None

    # Table header parameters
    header: dict = Field(default_factory=dict)

    read_only: bool = False
    default: Any | None = None
    required: bool = False

    max_length: int | None = None
    min_length: int | None = None

    choices: List[dict] | None = None

    tag_colors: dict | None = None
    variant: str | None = None
    size: str | None = None

    preview_max_height: int | None = None
    preview_max_width: int | None = None


@dataclass
class FieldsSchemaData(DataclassBase):
    fields: Dict[str, FieldSchemaData] = Field(default_factory=dict)


# pylint: disable=too-many-instance-attributes
@dataclass
class TableInfoSchemaData(DataclassBase):
    table_schema: FieldsSchemaData

    search_enabled: bool
    search_help: str | None

    pk_name: str | None
    can_retrieve: bool

    can_create: bool
    can_update: bool

    table_filters: FieldsSchemaData | None = None

    ordering_fields: List[str] = Field(default_factory=list)

    actions: Dict[str, dict] | None = None


@dataclass
class GraphInfoSchemaData(DataclassBase):
    search_enabled: bool
    search_help: str | None

    table_filters: FieldsSchemaData | None = None


@dataclass
class CategorySchemaData(DataclassBase):
    title: str | None
    icon: str | None
    type: str

    table_info: TableInfoSchemaData | None = None
    graph_info: GraphInfoSchemaData | None = None


@dataclass
class Category(abc.ABC):
    slug: ClassVar[str]
    title: ClassVar[str | TranslateText | None] = None

    # https://pictogrammers.com/library/mdi/
    icon: ClassVar[str | None] = None

    _type_slug: ClassVar[str]

    def generate_schema(self, user: UserABC, language_manager: LanguageManager) -> CategorySchemaData:
        return CategorySchemaData(
            title=language_manager.get_text(self.title) or self.slug,
            icon=self.icon,
            type=self._type_slug,
        )
