import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from admin_panel.exceptions import AdminAPIException
from admin_panel.api.utils import get_category
from admin_panel.schema.graphs.category_graphs import CategoryGraphs, GraphData, GraphsDataResult

router = APIRouter(prefix="/graph", tags=["graph"])

logger = logging.getLogger('admin_panel')


@router.post(path='/{group}/{category}/')
async def graph_data(request: Request, group: str, category: str, data: GraphData) -> GraphsDataResult:
    schema_category, user = await get_category(request, group, category, check_type=CategoryGraphs)

    result: GraphsDataResult = await schema_category.get_data(data, user)

    try:
        return JSONResponse(content=result.dict())
    except AdminAPIException as e:
        return JSONResponse(e.get_error().model_dump(mode='json'), status_code=e.status_code)
