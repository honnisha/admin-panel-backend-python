from fastapi import APIRouter

from .views.schema import router as schema_router
from .views.table import router as schema_table
from .views.auth import router as schema_auth
from .views.autocomplete import router as schema_autocomplete
from .views.graphs import router as schema_graphs
from .views.index import router as schema_index

admin_panel_router = APIRouter()
admin_panel_router.include_router(schema_router)
admin_panel_router.include_router(schema_table)
admin_panel_router.include_router(schema_auth)
admin_panel_router.include_router(schema_autocomplete)
admin_panel_router.include_router(schema_graphs)
admin_panel_router.include_router(schema_index)
