from fastapi import APIRouter

from .views.schema import router as schema_router
from .views.table import router as schema_table

admin_panel_router = APIRouter()
admin_panel_router.include_router(schema_router)
admin_panel_router.include_router(schema_table)
