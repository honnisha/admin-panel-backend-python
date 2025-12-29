from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from admin_panel.api.utils import get_category
from admin_panel.exceptions import AdminAPIException
from admin_panel.schema.admin_schema import AdminSchema
from admin_panel.schema.table.table_models import AutocompleteData, AutocompleteResult
from admin_panel.translations import LanguageManager
from admin_panel.utils import get_logger

router = APIRouter(prefix="/autocomplete", tags=["Autocomplete"])

logger = get_logger()


@router.post(path='/{group}/{category}/')
async def autocomplete(request: Request, group: str, category: str, data: AutocompleteData):
    schema: AdminSchema = request.app.state.schema
    schema_category, user = await get_category(request, group, category)

    language_slug = request.headers.get('Accept-Language')
    language_manager: LanguageManager = schema.get_language_manager(language_slug)
    context = {'language_manager': language_manager}

    try:
        result: AutocompleteResult = await schema_category.autocomplete(data, user, language_manager)
    except AdminAPIException as e:
        return JSONResponse(e.get_error().model_dump(mode='json', context=context), status_code=e.status_code)

    return JSONResponse(result.model_dump(mode='json', context=context))
