from typing import Any, AsyncIterator, Dict, List, Optional, Protocol


class AnswerEnginePort(Protocol):
    async def answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> Dict[str, Any]:
        """Generate a grounded answer for a query."""

    def stream_answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a grounded answer for a query."""


class SearchEnginePort(Protocol):
    def search(
        self,
        query: str,
        top_k: int,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search the knowledge base."""


class IndexBuilderPort(Protocol):
    def load_or_build(self) -> Any:
        """Load a usable index or build one when necessary."""

    def build(self, force: bool = False) -> Any:
        """Build or load an index according to the requested policy."""

    def status(self) -> Dict[str, Any]:
        """Return index metadata for health and administration APIs."""
