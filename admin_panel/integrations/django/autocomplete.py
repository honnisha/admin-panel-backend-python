from admin_panel.auth import UserABC
from admin_panel.schema.table.table_models import AutocompleteData, AutocompleteResult


class DjangoAdminAutocomplete:

    def get_model(self):
        return None

    async def autocomplete(self, data: AutocompleteData, user: UserABC) -> AutocompleteResult:
        form_schema = None

        if data.action_name is not None:
            action_fn = self._get_action_fn(data.action_name)
            if not action_fn:
                raise Exception(f'Action "{data.action_name}" is not found')

            if not action_fn.form_schema:
                raise Exception(f'Action "{data.action_name}" form_schema is None')

            form_schema = action_fn.form_schema

        elif data.is_filter:
            if not self.table_filters:
                raise Exception(f'Action "{data.action_name}" table_filters is None')

            form_schema = self.table_filters

        else:
            form_schema = self.table_schema

        field = form_schema.get_field(data.field_slug)
        if not field:
            raise Exception(f'Field "{data.field_slug}" is not found')

        results = await field.autocomplete(self.get_model(), data, user)
        return AutocompleteResult(results=results)
