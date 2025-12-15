import abc
import dataclasses
import inspect
from typing import ClassVar, Dict

import pydantic

from admin_panel.utils import DataclassBase


@pydantic.dataclasses.dataclass
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

    def translate_dataclass(self, data):
        if not dataclasses.is_dataclass(data):
            return

        for field in dataclasses.fields(type(data)):
            value = getattr(data, field.name, None)

            if issubclass(type(value), TranslateText):
                setattr(data, field.name, self.get_text(value))

            if isinstance(value, dict):
                for k, v in value.items():
                    self.translate_dataclass(v)
                continue

            self.translate_dataclass(value)
