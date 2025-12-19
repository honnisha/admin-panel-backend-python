import abc
from typing import ClassVar, Dict

import pydantic
from asgiref.local import Local

from admin_panel.utils import DataclassBase

_active = Local()


@pydantic.dataclasses.dataclass
class TranslateText(DataclassBase):
    slug: str
    translation_kwargs: dict | None = None

    def __init__(self, slug: str):
        self.slug = slug

    @pydantic.model_serializer(mode='plain')
    def serialize_model(self, info: pydantic.SerializationInfo) -> str:
        ctx = info.context or {}
        language_manager = ctx.get('language_manager')

        if not language_manager:
            raise AttributeError('language_manager is not in context manager for serialization')

        if not issubclass(type(language_manager), LanguageManager):
            raise AttributeError(f'language_manager "{type(language_manager)}" is not subclass of LanguageManager')

        return language_manager.get_text(self)

    def __str__(self):
        lm = getattr(_active, '_language_manager', None)
        if not lm:

            raise AttributeError(f'language_manager is not in local scope for translation: {locals()}')

        if not issubclass(type(lm), LanguageManager):
            raise AttributeError(f'language_manager "{lm}" is not subclass of LanguageManager')

        return lm.get_text(self)

    def __mod__(self, other):
        if not isinstance(other, dict):
            raise AttributeError('TranslateText only dict is supported trough % operand')
        self.translation_kwargs = other
        return self


class LanguageManager(abc.ABC):
    language: str | None

    languages: ClassVar[Dict[str, str | TranslateText] | None] = None
    languages_phrases: ClassVar[dict | None] = None

    def __init__(self, language: str | None):
        self.language = language
        _active._language_manager = self

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
