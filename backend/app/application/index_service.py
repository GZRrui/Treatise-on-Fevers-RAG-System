import asyncio
from typing import Any, Dict

from backend.app.domain.ports import IndexBuilderPort


class IndexService:
    """Application use cases for loading and rebuilding the knowledge index."""

    def __init__(self, builder: IndexBuilderPort):
        self._builder = builder
        self._lock = asyncio.Lock()
        self._current_index: Any = None

    @property
    def current_index(self) -> Any:
        return self._current_index

    async def initialize(self) -> Any:
        async with self._lock:
            self._current_index = await asyncio.to_thread(self._builder.load_or_build)
            return self._current_index

    async def build(self, force: bool = False) -> Dict[str, Any]:
        async with self._lock:
            self._current_index = await asyncio.to_thread(self._builder.build, force)
            return self._builder.status()

    def status(self) -> Dict[str, Any]:
        return self._builder.status()
