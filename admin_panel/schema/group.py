import abc
from typing import List

from pydantic.dataclasses import dataclass

from admin_panel.auth import UserABC
from admin_panel.schema.category import Category
from admin_panel.translations import LanguageManager, TranslateText


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

    def generate_schema(self, user: UserABC, language_manager: LanguageManager) -> dict:
        result = {
            'title': language_manager.get_text(self.title) or self.slug,
            'icon': self.icon,
            'categories': {},
        }
        for category in self.categories:

            if not category.slug:
                msg = f'Category {type(category).__name__}.slug is empty'
                raise AttributeError(msg)

            if category.slug in result['categories']:
                raise KeyError(f'Group slug:"{self.slug}" already have category slug:"{category.slug}"')

            result['categories'][category.slug] = category.generate_schema(user, language_manager)

        return result

    def get_category(self, category_slug: str) -> Category | None:
        for category in self.categories:
            if category.slug == category_slug:
                return category

        return None
