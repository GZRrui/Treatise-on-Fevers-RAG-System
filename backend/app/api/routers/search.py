from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_search_service
from backend.app.api.schemas.requests import SearchRequest
from backend.app.api.schemas.responses import SearchResponse
from backend.app.application.search_service import SearchService

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_articles(
    request: SearchRequest,
    service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResponse:
    results = service.search(
        query=request.query,
        top_k=request.top_k,
        category=request.category,
    )
    return SearchResponse.from_domain(results)
