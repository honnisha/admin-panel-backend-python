import json
import logging
import urllib
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from admin_panel.api.api_exception import AdminAPIErrorModel, AdminAPIException
from admin_panel.controllers import AdminAuthentication
from admin_panel.schema.table.admin_action import ActionData, ActionResult
from admin_panel.schema.table.category_table import CategoryTable
from admin_panel.schema.table.table_models import (
    AutocompleteData,
    AutocompleteResult,
    CreateResult,
    ListData,
    ListFilters,
    TableListResult,
    UpdateResult,
)

router = APIRouter(prefix="/table", tags=["table"])

logger = logging.getLogger('admin_panel')


async def get_user(request):
    auth: AdminAuthentication = request.app.state.auth
    try:
        user = await auth.authenticate(request.headers)
    except AdminAPIException as e:
        return JSONResponse(e.get_error(), status_code=e.status_code)

    return user


async def get_table_category(request, group: str, category: str) -> CategoryTable:
    user = await get_user(request)

    schema_group = request.app.state.schema.get_group(group)
    if not schema_group:
        raise HTTPException(status_code=404, detail="Group not found")

    schema_category = schema_group.get_category(category)
    if not schema_category:
        raise HTTPException(status_code=404, detail="Category not found")

    if not issubclass(schema_category.__class__, CategoryTable):
        raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not a table")

    return schema_category, user


# pylint: disable=too-many-arguments
@router.post(path='/{group}/{category}/list/')
async def table_list(request: Request, group: str, category: str, list_data: ListData):
    schema_category, user = await get_table_category(request, group, category)
    result: TableListResult = await schema_category.get_list(list_data, user)

    try:
        return JSONResponse(content=result.asdict())
    except Exception as e:
        logger.exception('Admin list error: %s; result: %s', e, result)
        raise HTTPException(status_code=500, detail=f"Content error: {e}") from e


@router.post(path='/{group}/{category}/retrieve/{pk}/')
async def table_retrieve(request: Request, group: str, category: str, pk: Any):
    schema_category, user = await get_table_category(request, group, category)
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
    schema_category, user = await get_table_category(request, group, category)
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
    schema_category, user = await get_table_category(request, group, category)
    if not schema_category.has_update:
        raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not allowed for update")

    try:
        result: UpdateResult = await schema_category.update(pk, await request.json(), user)
    except AdminAPIException as e:
        return JSONResponse(e.get_error(), status_code=e.status_code)

    return JSONResponse(content=result.dict())


@router.post(path='/{group}/{category}/action/{action}/')
async def table_action(request: Request, group: str, category: str, action: str, action_data: ActionData):
    schema_category, user = await get_table_category(request, group, category)

    result: ActionResult = await schema_category._perform_action(action, action_data)  # pylint: disable=protected-access
    return JSONResponse(content=result.asdict())


@router.post(path='/{group}/{category}/autocomplete/')
async def table_autocomplete(request: Request, group: str, category: str, data: AutocompleteData):
    schema_category, user = await get_table_category(request, group, category)

    result: AutocompleteResult = await schema_category._autocomplete(data)  # pylint: disable=protected-access
    return JSONResponse(content=result.dict())
