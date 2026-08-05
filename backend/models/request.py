"""Compatibility imports for API request schemas."""

from backend.app.api.schemas.requests import BuildIndexRequest, QARequest, SearchRequest

QAStreamRequest = QARequest

__all__ = ["BuildIndexRequest", "QARequest", "QAStreamRequest", "SearchRequest"]
