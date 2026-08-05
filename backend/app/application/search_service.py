from typing import Any, Dict, List, Optional

from backend.app.domain.ports import SearchEnginePort


class SearchService:
    """Application use case for knowledge-base search."""

    def __init__(self, engine: SearchEnginePort):
        self._engine = engine

    def search(
        self,
        query: str,
        top_k: int,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._engine.search(
            query=query,
            top_k=top_k,
            category=category,
        )
