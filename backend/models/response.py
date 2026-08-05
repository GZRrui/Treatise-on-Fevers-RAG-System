"""Compatibility imports for API response schemas."""

from pydantic import BaseModel

from backend.app.api.schemas.responses import (
    ArticleSource,
    ErrorResponse,
    QAData,
    QAResponse,
    SearchData,
    SearchResponse,
)


class BaseResponse(BaseModel):
    code: int = 200
    message: str = "success"


SearchResultItem = ArticleSource

__all__ = [
    "ArticleSource",
    "BaseResponse",
    "ErrorResponse",
    "QAData",
    "QAResponse",
    "SearchData",
    "SearchResponse",
    "SearchResultItem",
]
