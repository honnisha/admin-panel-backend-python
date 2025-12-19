import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from admin_panel.schema import AdminSchema

router = APIRouter()

templates = Jinja2Templates(directory='admin_panel/templates')


# Всё, что не должно попадать в SPA (можете расширять список)
EXACT_BLOCK = {"/openapi.json"}
PREFIX_BLOCK = ("/docs", "/redoc", "/scalar", "/static")


@router.get('/{rest_of_path:path}', response_class=HTMLResponse, include_in_schema=False)
async def admin_index(request: Request, rest_of_path: str):

    path = "/" + rest_of_path
    if path in EXACT_BLOCK or path.startswith(PREFIX_BLOCK):
        raise HTTPException(status_code=404)

    schema: AdminSchema = request.app.state.schema
    return templates.TemplateResponse(
        request=request, name='index.html', context={
            'title': schema.title,
            'favicon_image': schema.favicon_image,
            'settings_json': json.dumps(await schema.get_settings(request)),
        }
    )
