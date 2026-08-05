from backend.app.application.index_service import IndexService
from backend.app.application.qa_service import QAService
from backend.app.application.search_service import SearchService
from backend.app.domain.errors import ApplicationNotReadyError
from backend.app.infrastructure.rag.legacy_adapter import (
    LegacyIndexBuilder,
    LlamaIndexQAEngineAdapter,
)
from src.data_loader import DataLoader
from src.indexer import Indexer
from src.qa_engine import QAEngine


class ApplicationContainer:
    """Composition root for application dependencies and lifecycle state."""

    def __init__(self):
        self.index_service: IndexService | None = None
        self.qa_service: QAService | None = None
        self.search_service: SearchService | None = None
        self._qa_adapter: LlamaIndexQAEngineAdapter | None = None

    @property
    def ready(self) -> bool:
        return (
            self.qa_service is not None
            and self.index_service is not None
            and self.index_service.current_index is not None
        )

    @property
    def qa_engine(self) -> QAEngine:
        if self._qa_adapter is None:
            raise ApplicationNotReadyError("QA engine is not initialized")
        return self._qa_adapter.engine

    async def initialize(self) -> None:
        if self.index_service is None:
            loader = DataLoader()
            indexer = Indexer()
            self.index_service = IndexService(LegacyIndexBuilder(loader, indexer))
        index = await self.index_service.initialize()
        self._replace_qa_service(index)

    async def rebuild_index(self, force: bool = False):
        index_service = self.require_index_service()
        index_status = await index_service.build(force=force)
        self._replace_qa_service(index_service.current_index)
        return index_status

    def require_qa_service(self) -> QAService:
        if self.qa_service is None:
            raise ApplicationNotReadyError("QA service is not initialized")
        return self.qa_service

    def require_index_service(self) -> IndexService:
        if self.index_service is None:
            raise ApplicationNotReadyError("Index service is not initialized")
        return self.index_service

    def require_search_service(self) -> SearchService:
        if self.search_service is None:
            raise ApplicationNotReadyError("Search service is not initialized")
        return self.search_service

    def _replace_qa_service(self, index) -> None:
        adapter = LlamaIndexQAEngineAdapter(QAEngine(index))
        self._qa_adapter = adapter
        self.qa_service = QAService(adapter)
        self.search_service = SearchService(adapter)
