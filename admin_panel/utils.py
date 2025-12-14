import abc

from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass


class DataclassBase:
    def model_dump(self, *args, **kwargs) -> dict:
        adapter = TypeAdapter(type(self))
        return adapter.dump_python(self, *args, **kwargs)


@dataclass
class TranslateText(DataclassBase):
    slug: str

    def __init__(self, slug: str):
        self.slug = slug


class LanguageManager(abc.ABC):
    language: str | None

    def __init__(self, language: str | None):
        self.language = language

    def get_text(self, text: str | TranslateText | None) -> str:
        if isinstance(text, TranslateText):
            return text.slug
        return text
