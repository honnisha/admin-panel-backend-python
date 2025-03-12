import json
import urllib
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from admin_panel.table_schema import ActionData, ActionResult, CategoryTable, ListData, ListFilters, TableListResult

router = APIRouter(prefix="/table", tags=["table"])


def get_table_category(schema, group: str, category: str) -> CategoryTable:
    schema_group = schema.get_group(group)
    if not schema_group:
        raise HTTPException(status_code=404, detail="Group not found")

    schema_category = schema_group.get_category(category)
    if not schema_category:
        raise HTTPException(status_code=404, detail="Category not found")

    if not issubclass(schema_category.__class__, CategoryTable):
        raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not a table")

    return schema_category


# pylint: disable=too-many-arguments
@router.get(path='/{group}/{category}/')
async def table_list(
        request: Request,
        group: str,
        category: str,
        page: int = 1,
        limit: int = 25,
        search: str | None = None,
        ordering: str | None = None,
        filters: str | None = None,
):
    schema_category = get_table_category(request.app.state.schema, group, category)

    filters_data = ListFilters(search=None, filters={})
    if filters:
        filters_data = json.loads(urllib.parse.unquote(filters))
        filters_data = ListFilters(**filters_data)

    list_data = ListData(
        page=page,
        limit=limit,
        search=search,
        ordering=ordering,
        filters=filters_data,
    )
    result: TableListResult = await schema_category.get_list(list_data)
    return JSONResponse(content=result.asdict())


@router.get(path='/{group}/{category}/retrive/{pk}/')
async def table_retrive(request: Request, group: str, category: str, pk: Any):
    schema_category = get_table_category(request.app.state.schema, group, category)
    if not schema_category.has_retrieve:
        raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not allowed for retrive")

    data = schema_category.retrieve(pk)
    if data is None:
        raise HTTPException(status_code=404, detail=f"PK \"{pk}\" is not found")

    return JSONResponse(content=data)


@router.post(path='/{group}/{category}/create/')
async def table_create(request: Request, group: str, category: str):
    schema_category = get_table_category(request.app.state.schema, group, category)
    if not schema_category.has_create:
        raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not allowed for create")

    schema_category.create(request.body())


@router.patch(path='/{group}/{category}/update/{pk}/')
async def table_update(request: Request, group: str, category: str, pk: Any):
    schema_category = get_table_category(request.app.state.schema, group, category)
    if not schema_category.has_update:
        raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not allowed for update")

    schema_category.update(pk, request.body())


@router.post(path='/{group}/{category}/action/{action}/')
async def table_action(request: Request, group: str, category: str, action: str, action_data: ActionData):
    schema_category = get_table_category(request.app.state.schema, group, category)

    result: ActionResult = await schema_category._perform_action(action, action_data)  # pylint: disable=protected-access
    return JSONResponse(content=result.asdict())
