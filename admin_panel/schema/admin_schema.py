import importlib.metadata
from typing import List, Optional, Type
from urllib.parse import urljoin

from fastapi import Request
from pydantic.dataclasses import dataclass

from admin_panel.auth import UserABC
from admin_panel.schema.group import Group
from admin_panel.translations import LanguageManager, TranslateText
from admin_panel.utils import DataclassBase


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
        language_manager: LanguageManager = self.get_language_manager(language_slug)

        groups = {}

        for group in self.groups:
            if not group.slug:
                msg = f'Category group {type(group).__name__}.slug is empty'
                raise AttributeError(msg)

            groups[group.slug] = group.generate_schema(user, language_manager)

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
