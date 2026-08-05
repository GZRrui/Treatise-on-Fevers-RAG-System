from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_container, get_index_service
from backend.app.api.schemas.requests import BuildIndexRequest
from backend.app.api.schemas.responses import IndexBuildResponse, IndexStatusResponse
from backend.app.application.index_service import IndexService
from backend.app.container import ApplicationContainer

router = APIRouter()


@router.post("/index/build", response_model=IndexBuildResponse)
async def build_index(
    request: BuildIndexRequest = BuildIndexRequest(),
    container: ApplicationContainer = Depends(get_container),
) -> IndexBuildResponse:
    info = await container.rebuild_index(force=request.force)
    return IndexBuildResponse(
        message="索引构建成功" if request.force else "索引更新成功",
        data={
            "exists": info.get("exists", True),
            "vector_count": info.get("vector_count", 0),
            "storage_path": info.get("storage_path", ""),
        },
    )


@router.get("/index/status", response_model=IndexStatusResponse)
async def get_index_status(
    service: IndexService = Depends(get_index_service),
) -> IndexStatusResponse:
    info = service.status()
    if not info.get("exists", False):
        return IndexStatusResponse(exists=False, status="not_ready")
    return IndexStatusResponse(
        exists=True,
        vector_count=info.get("vector_count", 0),
        storage_path=info.get("storage_path", ""),
        embedding_model=info.get("embedding_model", ""),
        embedding_dim=info.get("embedding_dim", 0),
        status="ready",
    )
