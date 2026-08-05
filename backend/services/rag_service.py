"""Backward-compatible facade for the application QA service."""

from typing import Any, Dict, List, Optional

from backend.app.application.qa_service import QAService
from backend.app.infrastructure.rag.legacy_adapter import LlamaIndexQAEngineAdapter
from src.data_loader import DataLoader
from src.qa_engine import QAEngine


class RAGService:
    """Compatibility facade kept for callers of the old service path."""

    def __init__(self, qa_engine: QAEngine):
        self._adapter = LlamaIndexQAEngineAdapter(qa_engine)
        self._service = QAService(self._adapter)

    @property
    def retriever(self):
        return self._adapter.engine.retriever

    async def answer(
        self,
        query: str,
        top_k: int = 5,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        return await self._service.answer(query, top_k, include_sources)

    async def stream_answer(self, query: str, top_k: int = 5):
        async for chunk in self._service.stream_answer(query, top_k, True):
            yield chunk

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._adapter.search(query, top_k, category)

    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        for article in DataLoader().load_clean_data():
            if int(article.get("id", 0)) == article_id:
                return article
        return None

    def get_chapters(self) -> List[str]:
        data = DataLoader().load_clean_data()
        return sorted({article.get("chapter", "") for article in data if article.get("chapter")})

    def get_categories(self) -> List[str]:
        data = DataLoader().load_clean_data()
        return sorted({article.get("category", "") for article in data if article.get("category")})
