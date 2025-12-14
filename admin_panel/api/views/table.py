import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from admin_panel.api.api_exception import AdminAPIErrorModel, AdminAPIException
from admin_panel.api.utils import get_category
from admin_panel.schema.base import AdminSchema
from admin_panel.schema.table.admin_action import ActionData, ActionResult
from admin_panel.schema.table.category_table import CategoryTable
from admin_panel.schema.table.table_models import CreateResult, ListData, TableListResult, UpdateResult
from admin_panel.utils import LanguageManager

router = APIRouter(prefix="/table", tags=["table"])

logger = logging.getLogger('admin_panel')


# pylint: disable=too-many-arguments
@router.post(path='/{group}/{category}/list/')
async def table_list(request: Request, group: str, category: str, list_data: ListData):
    schema: AdminSchema = request.app.state.schema

    schema_category, user = await get_category(request, group, category, check_type=CategoryTable)

    language_slug = request.headers.get('Accept-Language')
    language: LanguageManager = schema.get_language_manager(language_slug)

    result: TableListResult = await schema_category.get_list(list_data, user, language)

    try:
        return JSONResponse(content=result.model_dump(mode='json'))
    except Exception as e:
        logger.exception('Admin list error: %s; result: %s', e, result)
        raise HTTPException(status_code=500, detail=f"Content error: {e}") from e


@router.post(path='/{group}/{category}/retrieve/{pk}/')
async def table_retrieve(request: Request, group: str, category: str, pk: Any):
    schema_category, user = await get_category(request, group, category, check_type=CategoryTable)
    if not schema_category.has_retrieve:
        raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not allowed for retrive")

    data: Optional[dict] = await schema_category.retrieve(pk, user)
    if data is None:
        raise HTTPException(status_code=404, detail=f"PK \"{pk}\" is not found")

    try:
        return JSONResponse(content=data)
    except Exception as e:
        logger.exception('Admin retrieve error: %s; result: %s', e, data)
        raise HTTPException(status_code=500, detail=f"Content error: {e}") from e


@router.post(
    path='/{group}/{category}/create/',
    responses={400: {"model": AdminAPIErrorModel}},
)
async def table_create(request: Request, group: str, category: str):
    schema_category, user = await get_category(request, group, category, check_type=CategoryTable)
    if not schema_category.has_create:
        raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not allowed for create")

    try:
        result: CreateResult = await schema_category.create(await request.json(), user)
    except AdminAPIException as e:
        return JSONResponse(e.get_error(), status_code=e.status_code)

    return JSONResponse(content=result.dict())


@router.patch(
    path='/{group}/{category}/update/{pk}/',
    responses={400: {"model": AdminAPIErrorModel}},
)
async def table_update(request: Request, group: str, category: str, pk: Any) -> UpdateResult:
    schema_category, user = await get_category(request, group, category, check_type=CategoryTable)
    if not schema_category.has_update:
        raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not allowed for update")

    try:
        result: UpdateResult = await schema_category.update(pk, await request.json(), user)
    except AdminAPIException as e:
        return JSONResponse(e.get_error(), status_code=e.status_code)

    return JSONResponse(content=result.dict())


@router.post(path='/{group}/{category}/action/{action}/')
async def table_action(request: Request, group: str, category: str, action: str, action_data: ActionData):
    schema: AdminSchema = request.app.state.schema

    schema_category, _user = await get_category(request, group, category, check_type=CategoryTable)

    language_slug = request.headers.get('Accept-Language')
    language: LanguageManager = schema.get_language_manager(language_slug)

    # pylint: disable=protected-access
    result: ActionResult = await schema_category._perform_action(action, action_data, language)
    return JSONResponse(content=result.model_dump(mode='json'))
