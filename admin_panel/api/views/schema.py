from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/schema", tags=["schema"])


@router.get(path='')
def schema(request: Request):
    return JSONResponse(content=request.app.state.schema.generate_schema())
