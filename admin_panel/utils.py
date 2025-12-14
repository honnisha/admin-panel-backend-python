import abc
from typing import ClassVar, Dict

from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass


class DataclassBase:
    def model_dump(self, *args, **kwargs) -> dict:
        adapter = TypeAdapter(type(self))
        return adapter.dump_python(self, *args, **kwargs)


@dataclass
class TranslateText(DataclassBase):
    slug: str
    translation_kwargs: dict | None = None

    def __init__(self, slug: str):
        self.slug = slug

    def __mod__(self, other):
        if not isinstance(other, dict):
            raise AttributeError('TranslateText only supports dict trough % operand')
        self.translation_kwargs = other
        return self


class LanguageManager(abc.ABC):
    language: str | None

    languages: ClassVar[Dict[str, str | TranslateText] | None] = None
    languages_phrases: ClassVar[dict | None] = None

    def __init__(self, language: str | None):
        self.language = language

    def get_text(self, text) -> str:
        if self.languages_phrases and isinstance(text, TranslateText):
            default_lang = list(self.languages_phrases.keys())[0]

            phrases = self.languages_phrases.get(self.language or default_lang)
            if not phrases:
                phrases = self.languages_phrases[default_lang]

            translation = phrases.get(text.slug) or text.slug
            if text.translation_kwargs:
                translation %= text.translation_kwargs
            return translation

        return text
