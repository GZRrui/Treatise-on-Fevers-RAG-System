
from backend.app.domain.ports import SearchEnginePort
from backend.app.domain.retrieval import SearchResult


class SearchService:
    """Application use case for knowledge-base search."""

    def __init__(self, engine: SearchEnginePort):
        self._engine = engine

    def search(
        self,
        query: str,
        top_k: int,
        category: str | None = None,
    ) -> SearchResult:
        return self._engine.search(
            query=query,
            top_k=top_k,
            category=category,
        )
