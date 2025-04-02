from admin_panel.schema.base import Category
from admin_panel.schema.table.fields_schema import FieldsSchema


class CategoryGraphs(Category):
    type_slug: str = 'graphs'

    search_enabled: bool = False
    search_help: str | None = None

    table_filters: FieldsSchema | None = None

    def generate_schema(self, user) -> dict:
        schema = super().generate_schema(user)
        graph = {}

        graph['search_enabled'] = self.search_enabled
        graph['search_help'] = self.search_help

        graph['table_filters'] = {}
        if self.table_filters:
            graph['table_filters'] = self.table_filters.generate_schema(user)

        schema['graph_info'] = graph
        return schema
