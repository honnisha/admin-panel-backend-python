import abc
from typing import ClassVar

from pydantic.dataclasses import dataclass

from admin_panel.auth import UserABC
from admin_panel.translations import LanguageManager, TranslateText


@dataclass
class Category(abc.ABC):
    slug: ClassVar[str]
    title: ClassVar[str | TranslateText | None] = None

    # https://pictogrammers.com/library/mdi/
    icon: ClassVar[str | None] = None

    _type_slug: ClassVar[str]

    def generate_schema(self, user: UserABC, language_manager: LanguageManager) -> dict:
        return {
            'title': language_manager.get_text(self.title) or self.slug,
            'icon': self.icon,
            'type': self._type_slug,
        }
