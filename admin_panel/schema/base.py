import abc
import importlib.metadata
from typing import ClassVar, List, Optional, Type
from urllib.parse import urljoin

from fastapi import Request
from pydantic.dataclasses import dataclass

from admin_panel.utils import DataclassBase, LanguageManager, TranslateText


@dataclass
class UserABC(DataclassBase, abc.ABC):
    username: str


@dataclass
class Category(abc.ABC):
    slug: ClassVar[str]
    title: ClassVar[str | TranslateText | None] = None

    # https://pictogrammers.com/library/mdi/
    icon: ClassVar[str | None] = None

    _type_slug: ClassVar[str]

    def generate_schema(self, user: UserABC, language: LanguageManager) -> dict:
        return {
            'title': language.get_text(self.title) or self.slug,
            'icon': self.icon,
            'type': self._type_slug,
        }


@dataclass
class Group(abc.ABC):
    categories: List[Category]
    slug: str
    title: str | TranslateText | None = None

    # https://pictogrammers.com/library/mdi/
    icon: str | None = None

    def __post_init__(self):
        for category in self.categories:
            if not issubclass(category.__class__, Category):
                raise TypeError(f'Category "{category}" is not instance of Category subclass')

    def generate_schema(self, user: UserABC, language: LanguageManager) -> dict:
        result = {
            'title': language.get_text(self.title) or self.slug,
            'icon': self.icon,
            'categories': {},
        }
        for category in self.categories:

            if not category.slug:
                msg = f'Category {type(category).__name__}.slug is empty'
                raise AttributeError(msg)

            if category.slug in result['categories']:
                raise KeyError(f'Group slug:"{self.slug}" already have category slug:"{category.slug}"')

            result['categories'][category.slug] = category.generate_schema(user, language)

        return result

    def get_category(self, category_slug: str) -> Optional[Category]:
        for category in self.categories:
            if category.slug == category_slug:
                return category

        return None


@dataclass
class AdminSchemaData(DataclassBase):
    groups: dict
    profile: UserABC


@dataclass
class AdminSchema:
    groups: List[Group]

    title: str | TranslateText | None = 'Admin'
    favicon_image: str = '/admin/static/favicon.ico'
    backend_prefix = None
    static_prefix = None

    language_manager_class: Type[LanguageManager] = LanguageManager

    def __post_init__(self):
        for group in self.groups:
            if not issubclass(group.__class__, Group):
                raise TypeError(f'Group "{group}" is not instance of Group subclass')

    def get_language_manager(self, language_slug: str | None) -> LanguageManager:
        return self.language_manager_class(language_slug)

    def generate_schema(self, user: UserABC, language_slug: str | None) -> AdminSchemaData:
        language: LanguageManager = self.get_language_manager(language_slug)

        groups = {}

        for group in self.groups:
            if not group.slug:
                msg = f'Category group {type(group).__name__}.slug is empty'
                raise AttributeError(msg)

            groups[group.slug] = group.generate_schema(user, language)

        return AdminSchemaData(
            groups=groups,
            profile=user,
        )

    def get_group(self, group_slug: str) -> Optional[Group]:
        for group in self.groups:
            if group.slug == group_slug:
                return group

        return None

    async def get_settings(self, request: Request):
        language_slug = request.headers.get('Accept-Language')
        language_manager: LanguageManager = self.get_language_manager(language_slug)

        backend_prefix = self.backend_prefix
        if not backend_prefix:
            backend_prefix = urljoin(str(request.base_url), '/admin/')

        static_prefix = self.static_prefix
        if not static_prefix:
            static_prefix = urljoin(str(request.base_url), '/admin/static/')

        languages = None
        if language_manager.languages:
            languages = {}
            for k, v in language_manager.languages.items():
                languages[k] = language_manager.get_text(v)

        return {
            'title': language_manager.get_text(self.title),
            'logo_image': None,
            'backend_prefix': backend_prefix,
            'static_prefix': static_prefix,
            'version': importlib.metadata.version('admin-panel'),
            'api_timeout_ms': 1000 * 5,
            'languages': languages,
        }
