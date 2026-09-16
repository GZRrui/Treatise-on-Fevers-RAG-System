from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from backend.app.api.dependencies import get_container
from backend.app.container import ApplicationContainer

router = APIRouter()


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "timestamp": _timestamp(),
        "service": "shanghanlun-rag",
        "version": "1.0.0",
    }


@router.get("/health/ready")
async def readiness_check(
    response: Response,
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> dict[str, str]:
    if not container.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "timestamp": _timestamp(),
            "service": "shanghanlun-rag",
        }
    return {
        "status": "ready",
        "timestamp": _timestamp(),
        "service": "shanghanlun-rag",
    }
