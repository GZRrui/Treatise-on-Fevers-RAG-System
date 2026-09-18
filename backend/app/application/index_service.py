import asyncio

from backend.app.domain.indexing import IndexStatus
from backend.app.domain.ports import IndexReaderPort


class IndexService:
    """Application use cases for loading and rebuilding the knowledge index."""

    def __init__(self, reader: IndexReaderPort):
        self._reader = reader
        self._lock = asyncio.Lock()
        self._current_index: object | None = None

    @property
    def current_index(self) -> object | None:
        return self._current_index

    async def initialize(self) -> object:
        async with self._lock:
            self._current_index = await asyncio.to_thread(
                self._reader.load_existing
            )
            return self._current_index

    def status(self) -> IndexStatus:
        return self._reader.status()
