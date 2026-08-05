"""Compatibility import for the modular API router."""

from backend.app.api.routers.index import router
from backend.app.api.schemas.requests import BuildIndexRequest
from backend.app.api.schemas.responses import IndexStatusResponse

__all__ = ["BuildIndexRequest", "IndexStatusResponse", "router"]
