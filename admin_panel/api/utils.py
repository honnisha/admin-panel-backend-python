from fastapi import HTTPException
from fastapi.responses import JSONResponse

from admin_panel.exceptions import AdminAPIException
from admin_panel.auth import AdminAuthentication


async def get_user(request):
    auth: AdminAuthentication = request.app.state.auth
    try:
        user = await auth.authenticate(request.headers)
    except AdminAPIException as e:
        return JSONResponse(e.get_error().model_dump(mode='json'), status_code=e.status_code)

    return user


async def get_category(request, group: str, category: str, check_type=None):
    user = await get_user(request)

    schema_group = request.app.state.schema.get_group(group)
    if not schema_group:
        raise HTTPException(status_code=404, detail="Group not found")

    schema_category = schema_group.get_category(category)
    if not schema_category:
        raise HTTPException(status_code=404, detail="Category not found")

    if check_type:
        schema_category, user = await get_category(request, group, category)
        if not issubclass(schema_category.__class__, check_type):
            raise HTTPException(status_code=404, detail=f"Category {group}.{category} is not a {check_type.__name__}")

    return schema_category, user
