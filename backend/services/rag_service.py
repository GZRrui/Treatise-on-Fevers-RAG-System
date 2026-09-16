"""Backward-compatible facade for the application QA service."""

from typing import Any

from backend.app.application.qa_service import QAService
from backend.app.domain.qa import StreamEventType
from backend.app.domain.retrieval import ArticleSource
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
    ) -> dict[str, Any]:
        result = await self._service.answer(query, top_k, include_sources)
        return {
            "answer": result.answer,
            "query": result.query,
            "sources": [_source_to_dict(item) for item in result.sources],
            "source_count": result.source_count,
        }

    async def stream_answer(self, query: str, top_k: int = 5):
        async for event in self._service.stream_answer(query, top_k, True):
            if event.type is StreamEventType.SOURCES:
                yield {
                    "type": "sources",
                    "data": [_source_to_dict(item) for item in event.sources],
                    "source_count": len(event.sources),
                }
            elif event.type is StreamEventType.CONTENT:
                yield {"type": "content", "data": event.content}
            elif event.type is StreamEventType.END:
                yield {
                    "type": "done",
                    "data": event.content,
                    "query": event.query,
                }

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        result = self._adapter.search(query, top_k, category)
        return [_source_to_dict(item) for item in result.items]

    def get_article_by_id(self, article_id: int) -> dict[str, Any] | None:
        for article in DataLoader().load_clean_data():
            if int(article.get("id", 0)) == article_id:
                return article
        return None

    def get_chapters(self) -> list[str]:
        data = DataLoader().load_clean_data()
        return sorted(
            {
                article.get("chapter", "")
                for article in data
                if article.get("chapter")
            }
        )

    def get_categories(self) -> list[str]:
        data = DataLoader().load_clean_data()
        return sorted(
            {
                article.get("category", "")
                for article in data
                if article.get("category")
            }
        )


def _source_to_dict(source: ArticleSource) -> dict[str, Any]:
    return {
        "id": source.id,
        "standard_id": source.standard_id,
        "chapter": source.chapter,
        "section": source.section,
        "category": source.category,
        "text": source.text,
        "score": source.score,
        "formulas": list(source.formulas),
    }
