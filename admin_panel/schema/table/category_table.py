import abc
import asyncio
import copy
from typing import Awaitable, List

from fastapi import HTTPException

from admin_panel.schema.base import Category, UserABC
from admin_panel.schema.table.admin_action import ActionData, ActionResult
from admin_panel.schema.table.fields_schema import FieldsSchema
from admin_panel.schema.table.table_models import AutocompleteData, AutocompleteResult, ListData, TableListResult
from admin_panel.utils import LanguageManager, TranslateText


class CategoryTable(Category):
    _type_slug: str = 'table'

    search_enabled: bool = False
    search_help: str | TranslateText | None = None

    table_schema: FieldsSchema
    table_filters: FieldsSchema | None = None

    ordering_fields: List[str] = []

    pk_name: str = 'id'

    def __init__(self):
        if self.slug is None:
            msg = f'Category table attribute {type(self).__name__}.slug must be set'
            raise Exception(msg)

    @property
    def has_retrieve(self):
        fn = getattr(self, 'retrieve', None)
        return asyncio.iscoroutinefunction(fn)

    @property
    def has_create(self):
        fn = getattr(self, 'create', None)
        return asyncio.iscoroutinefunction(fn)

    @property
    def has_update(self):
        fn = getattr(self, 'update', None)
        return asyncio.iscoroutinefunction(fn)

    def generate_schema(self, user, language: LanguageManager) -> dict:
        schema = super().generate_schema(user, language)
        table = {}

        table_schema = getattr(self, 'table_schema', None)
        if not table_schema or not issubclass(table_schema.__class__, FieldsSchema):
            raise AttributeError(f'Admin category {self.__class__} must have table_schema instance of FieldsSchema')

        table['table_schema'] = self.table_schema.generate_schema(user, language)
        table['ordering_fields'] = self.ordering_fields

        table['search_enabled'] = self.search_enabled
        table['search_help'] = language.get_text(self.search_help)

        table['pk_name'] = self.pk_name
        table['can_retrieve'] = self.has_retrieve

        table['can_create'] = self.has_create
        table['can_update'] = self.has_update

        table['table_filters'] = {}
        if self.table_filters:
            table['table_filters'] = self.table_filters.generate_schema(user, language)

        actions = {}
        for attribute_name in dir(self):
            if '__' in attribute_name:
                continue

            attribute = getattr(self, attribute_name)
            if asyncio.iscoroutinefunction(attribute) and getattr(attribute, '__action__', False):
                action = copy.copy(attribute.action_info)

                action['title'] = language.get_text(action.get('title'))
                action['description'] = language.get_text(action.get('description'))
                action['confirmation_text'] = language.get_text(action.get('confirmation_text'))

                form_schema = action['form_schema']
                if form_schema:
                    try:
                        action['form_schema'] = form_schema.generate_schema(user, language)
                    except Exception as e:
                        msg = f'Action {attribute} form schema {form_schema} error: {e}'
                        raise Exception(msg) from e

                actions[attribute_name] = action

        table['actions'] = actions

        schema['table_info'] = table
        return schema

    def _get_action_fn(self, action: str) -> Awaitable | None:
        attribute = getattr(self, action)
        if not asyncio.iscoroutinefunction(attribute) or not getattr(attribute, '__action__', False):
            return None

        return attribute

    async def _perform_action(self, action: str, action_data: ActionData, language: LanguageManager) -> ActionResult:
        action_fn = self._get_action_fn(action)
        if action_fn is None:
            raise HTTPException(status_code=404, detail=f"Action \"{action}\" is not found")

        try:
            result: ActionResult = await action_fn(action_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Action \"{action}\" error: {e}") from e

        if result.message:
            result.message.text = language.get_text(result.message.text)

        result.persistent_message = language.get_text(result.persistent_message)

        return result

    async def autocomplete(self, data: AutocompleteData, user: UserABC) -> AutocompleteResult:
        """
        Retrieves list of found options to select.
        """
        raise NotImplementedError('autocomplete is not implemented')

    # pylint: disable=too-many-arguments
    @abc.abstractmethod
    async def get_list(self, list_data: ListData, user: UserABC, language: LanguageManager) -> TableListResult:
        raise NotImplementedError()

#     async def retrieve(self, pk: Any, user: UserABC) -> Optional[dict]:
#        raise NotImplementedError()

#    async def create(self, data: dict, user: UserABC) -> CreateResult:
#        raise NotImplementedError()

#    async def update(self, pk: Any, data: dict, user: UserABC) -> UpdateResult:
#        raise NotImplementedError()
