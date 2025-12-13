import abc
from dataclasses import dataclass
from typing import List, Optional


class UserABC(abc.ABC):
    username: str


class Category(abc.ABC):
    slug: str = None
    title: str | None = None

    # https://pictogrammers.com/library/mdi/
    icon: str | None = None

    type_slug: str = 'table'

    def generate_schema(self, user) -> dict:
        return {
            'title': self.title or self.slug,
            'icon': self.icon,
            'type': self.type_slug,
        }


@dataclass
class Group(abc.ABC):
    categories: List[Category]
    slug: str
    title: str | None = None

    # https://pictogrammers.com/library/mdi/
    icon: str | None = None

    def __post_init__(self):
        for category in self.categories:
            if not issubclass(category.__class__, Category):
                raise TypeError(f'Category "{category}" is not instance of Category subclass')

    def generate_schema(self, user) -> dict:
        result = {
            'title': self.title or self.slug,
            'icon': self.icon,
            'categories': {},
        }
        for category in self.categories:
            if category.slug in result['categories']:
                raise KeyError(f'Group slug:"{self.slug}" already have category slug:"{category.slug}"')

            result['categories'][category.slug] = category.generate_schema(user)

        return result

    def get_category(self, category_slug: str) -> Optional[Category]:
        for category in self.categories:
            if category.slug == category_slug:
                return category

        return None


@dataclass
class AdminSchema:
    groups: List[Group]

    def __post_init__(self):
        for group in self.groups:
            if not issubclass(group.__class__, Group):
                raise TypeError(f'Group "{group}" is not instance of Group subclass')

    def generate_schema(self, user) -> dict:
        groups = {
            group.slug: group.generate_schema(user)
            for group in self.groups
        }
        return {
            'groups': groups,
        }

    def get_group(self, group_slug: str) -> Optional[Group]:
        for group in self.groups:
            if group.slug == group_slug:
                return group

        return None
