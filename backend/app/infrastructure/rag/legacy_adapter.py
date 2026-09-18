from collections.abc import AsyncIterator
from typing import Any

from backend.app.domain.indexing import IndexState, IndexStatus
from backend.app.domain.qa import AnswerResult, StreamEvent, StreamEventType
from backend.app.domain.retrieval import ArticleSource, SearchResult
from src.indexer import Indexer
from src.qa_engine import QAEngine


class LegacyIndexReader:
    """Expose the existing file index as a read-only runtime dependency."""

    def __init__(self, indexer: Indexer):
        self._indexer = indexer

    def load_existing(self) -> object:
        return self._indexer.load_existing_index()

    def status(self) -> IndexStatus:
        info = self._indexer.get_index_info()
        if info.get("error"):
            return IndexStatus(
                state=IndexState.CORRUPT,
                detail=str(info["error"]),
            )
        if not info.get("exists", False):
            return IndexStatus(state=IndexState.MISSING)
        return IndexStatus(
            state=IndexState.READY,
            vector_count=int(info.get("vector_count", 0)),
            storage_uri=str(info.get("storage_path", "")),
            embedding_model=str(info.get("embedding_model", "")),
            embedding_dimension=int(info.get("embedding_dim", 0)),
        )


class LlamaIndexQAEngineAdapter:
    """Adapt the current QA engine to the application-layer contract."""

    def __init__(self, engine: QAEngine):
        self._engine = engine

    @property
    def engine(self) -> QAEngine:
        return self._engine

    async def answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AnswerResult:
        result = await self._engine.aanswer(
            query=query,
            top_k=top_k,
            return_sources=include_sources,
        )
        return AnswerResult(
            answer=str(result["answer"]),
            query=str(result["query"]),
            sources=self._sources(result.get("sources", [])),
        )

    async def stream_answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AsyncIterator[StreamEvent]:
        async for event in self._engine.astream_answer(
            query=query, top_k=top_k, return_sources=include_sources
        ):
            event_type = str(event.get("type", ""))
            if event_type == "sources":
                yield StreamEvent(
                    type=StreamEventType.SOURCES,
                    sources=self._sources(event.get("data", [])),
                )
            elif event_type == "content":
                yield StreamEvent(
                    type=StreamEventType.CONTENT,
                    content=str(event.get("data", "")),
                )
            elif event_type == "done":
                yield StreamEvent(
                    type=StreamEventType.END,
                    content=str(event.get("data", "")),
                    query=str(event.get("query", query)),
                )

    def search(
        self,
        query: str,
        top_k: int,
        category: str | None = None,
    ) -> SearchResult:
        results = self._engine.retriever.retrieve_as_dict(query, top_k=top_k)
        if category:
            results = [
                item
                for item in results
                if category in item.get("category", "")
                or category in item.get("section", "")
            ]
        return SearchResult(
            query=query,
            items=self._sources(results[:top_k]),
        )

    @staticmethod
    def _sources(items: list[dict[str, Any]]) -> tuple[ArticleSource, ...]:
        return tuple(
            ArticleSource(
                id=int(item.get("id", 0)),
                standard_id=int(item.get("standard_id", 0)),
                chapter=str(item.get("chapter", "")),
                section=str(item.get("section", "")),
                category=str(item.get("category", "")),
                text=str(item.get("text", "")),
                score=float(item.get("score", 0.0)),
                formulas=tuple(item.get("formulas", [])),
            )
            for item in items
        )
