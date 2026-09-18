from collections.abc import AsyncIterator

from backend.app.domain.ports import AnswerEnginePort
from backend.app.domain.qa import AnswerResult, StreamEvent


class QAService:
    """Application use cases for question answering."""

    def __init__(self, engine: AnswerEnginePort):
        self._engine = engine

    async def answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool = True,
    ) -> AnswerResult:
        return await self._engine.answer(
            query=query,
            top_k=top_k,
            include_sources=include_sources,
        )

    def stream_answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        return self._engine.stream_answer(
            query=query,
            top_k=top_k,
            include_sources=include_sources,
        )
