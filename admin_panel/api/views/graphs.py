from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from admin_panel.api.utils import get_category
from admin_panel.exceptions import AdminAPIException
from admin_panel.schema.admin_schema import AdminSchema
from admin_panel.schema.graphs.category_graphs import CategoryGraphs, GraphData, GraphsDataResult
from admin_panel.translations import LanguageManager
from admin_panel.utils import get_logger

router = APIRouter(prefix="/graph", tags=["Category - Graph"])

logger = get_logger()


@router.post(path='/{group}/{category}/')
async def graph_data(request: Request, group: str, category: str, data: GraphData) -> GraphsDataResult:
    schema: AdminSchema = request.app.state.schema
    schema_category, user = await get_category(request, group, category, check_type=CategoryGraphs)

    result: GraphsDataResult = await schema_category.get_data(data, user)

    language_slug = request.headers.get('Accept-Language')
    language_manager: LanguageManager = schema.get_language_manager(language_slug)
    context = {'language_manager': language_manager}

    try:
        return JSONResponse(result.model_dump(mode='json', context=context))
    except AdminAPIException as e:
        return JSONResponse(e.get_error().model_dump(mode='json', context=context), status_code=e.status_code)
