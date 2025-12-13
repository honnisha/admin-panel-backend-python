from admin_panel.schema.base import UserABC
from admin_panel.schema.table.table_models import AutocompleteData, AutocompleteResult


class SQLAlchemyAdminAutocompleteMixin:
    async def autocomplete(self, data: AutocompleteData, user: UserABC) -> AutocompleteResult:
        raise NotImplementedError('autocomplete is not implemented')
