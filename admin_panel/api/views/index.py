import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from admin_panel.schema import AdminSchema

router = APIRouter()

templates = Jinja2Templates(directory='admin_panel/templates')


@router.get('/{rest_of_path:path}', response_class=HTMLResponse)
async def admin_index(request: Request):
    schema: AdminSchema = request.app.state.schema
    return templates.TemplateResponse(
        request=request, name='index.html', context={
            'title': schema.title,
            'favicon_image': schema.favicon_image,
            'settings_json': json.dumps(await schema.get_settings(request)),
        }
    )
