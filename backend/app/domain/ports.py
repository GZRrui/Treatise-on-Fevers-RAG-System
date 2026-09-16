from collections.abc import AsyncIterator
from typing import Protocol

from backend.app.domain.indexing import IndexStatus
from backend.app.domain.qa import AnswerResult, StreamEvent
from backend.app.domain.retrieval import SearchResult


class AnswerEnginePort(Protocol):
    async def answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AnswerResult:
        """Generate a grounded answer for a query."""

    def stream_answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AsyncIterator[StreamEvent]:
        """Stream a grounded answer for a query."""


class SearchEnginePort(Protocol):
    def search(
        self,
        query: str,
        top_k: int,
        category: str | None = None,
    ) -> SearchResult:
        """Search the knowledge base."""


class IndexReaderPort(Protocol):
    def load_existing(self) -> object:
        """Load an existing index without rebuilding it."""

    def status(self) -> IndexStatus:
        """Return read-only index metadata."""
