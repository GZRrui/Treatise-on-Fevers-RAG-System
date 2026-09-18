from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_index_service
from backend.app.api.schemas.responses import IndexStatusResponse
from backend.app.application.index_service import IndexService

router = APIRouter()


@router.get("/index/status", response_model=IndexStatusResponse)
async def get_index_status(
    service: Annotated[IndexService, Depends(get_index_service)],
) -> IndexStatusResponse:
    return IndexStatusResponse.from_domain(service.status())
