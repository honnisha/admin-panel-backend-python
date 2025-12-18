from typing import List

from pydantic import BaseModel

from admin_panel.schema import Category
from admin_panel.schema.table.fields_schema import FieldsSchema
from admin_panel.schema.table.table_models import ListFilters
from admin_panel.translations import LanguageManager, TranslateText


class GraphData(BaseModel):
    filters: ListFilters


class ChartData(BaseModel):
    data: dict
    options: dict
    width: int | None = None
    height: int = 50
    type: str = 'line'


class GraphsDataResult(BaseModel):
    charts: List[ChartData]


class CategoryGraphs(Category):
    _type_slug: str = 'graphs'

    search_enabled: bool = False
    search_help: str | TranslateText | None = None

    table_filters: FieldsSchema | None = None

    def generate_schema(self, user, language_manager: LanguageManager) -> dict:
        schema = super().generate_schema(user, language_manager)
        graph = {}

        graph['search_enabled'] = self.search_enabled
        graph['search_help'] = language_manager.get_text(self.search_help)

        graph['table_filters'] = {}
        if self.table_filters:
            graph['table_filters'] = self.table_filters.generate_schema(user, language_manager)

        schema['graph_info'] = graph
        return schema

    async def get_data(self, data: GraphData, user) -> GraphsDataResult:
        raise NotImplementedError()
