import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from admin_panel.api.utils import get_category
from admin_panel.schema.table.table_models import AutocompleteData, AutocompleteResult

router = APIRouter(prefix="/autocomplete", tags=["autocomplete"])

logger = logging.getLogger('admin_panel')


@router.post(path='/{group}/{category}/')
async def autocomplete(request: Request, group: str, category: str, data: AutocompleteData):
    schema_category, user = await get_category(request, group, category)

    result: AutocompleteResult = await schema_category._autocomplete(data, user)  # pylint: disable=protected-access
    return JSONResponse(content=result.dict())
