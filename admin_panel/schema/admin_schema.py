from typing import Any, Dict, List, Optional, Type

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic.dataclasses import dataclass

from admin_panel.auth import UserABC
from admin_panel.docs import build_redoc_docs, build_scalar_docs
from admin_panel.schema.group import Group, GroupSchemaData
from admin_panel.translations import LanguageManager, TranslateText
from admin_panel.utils import DataclassBase


@dataclass
class AdminSchemaData(DataclassBase):
    groups: Dict[str, GroupSchemaData]
    profile: UserABC


# pylint: disable=too-many-instance-attributes
@dataclass
class AdminSettingsData(DataclassBase):
    title: str | TranslateText
    description: str | TranslateText | None
    login_greetings_message: str | TranslateText
    logo_image: str | None
    languages: Dict[str, str] | None


@dataclass
class AdminSchema:
    groups: List[Group]
    auth: Any

    title: str | TranslateText | None = 'Admin'
    description: str | TranslateText | None = None
    login_greetings_message: str | TranslateText | None = None

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

    async def get_settings(self, request: Request) -> AdminSettingsData:
        language_slug = request.headers.get('Accept-Language')
        language_manager: LanguageManager = self.get_language_manager(language_slug)

        languages = None
        if language_manager.languages:
            languages = {}
            for k, v in language_manager.languages.items():
                languages[k] = language_manager.get_text(v)

        return AdminSettingsData(
            title=self.title,
            description=self.description,
            login_greetings_message=self.login_greetings_message,
            logo_image=None,
            languages=languages,
        )

    def generate_app(self, use_scalar=False, debug=False, allow_cors=True) -> FastAPI:
        # pylint: disable=unused-variable
        language_manager = self.get_language_manager(language_slug=None)

        app = FastAPI(
            title=language_manager.get_text(self.title),
            description=language_manager.get_text(self.description),
            debug=debug,
            docs_url='/docs',
            redoc_url=None,
        )

        if allow_cors:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )

        app.mount("/static", StaticFiles(directory="admin_panel/static"), name="static")

        app.state.schema = self

        if use_scalar:
            app.include_router(build_scalar_docs(app))

        app.include_router(build_redoc_docs(app, redoc_url='/redoc'))

        # pylint: disable=import-outside-toplevel
        from admin_panel.api.routers import admin_panel_router
        app.include_router(admin_panel_router)

        return app
