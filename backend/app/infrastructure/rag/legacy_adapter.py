from typing import Any, Dict, List, Optional

from src.data_loader import DataLoader
from src.indexer import Indexer
from src.qa_engine import QAEngine


class LegacyIndexBuilder:
    """Adapt the current file-based index implementation to the domain port."""

    def __init__(self, loader: DataLoader, indexer: Indexer):
        self._loader = loader
        self._indexer = indexer

    def _load_clean_data(self) -> List[Dict[str, Any]]:
        try:
            return self._loader.load_clean_data()
        except FileNotFoundError:
            return self._loader.process()

    def load_or_build(self) -> Any:
        self._load_clean_data()
        return self._indexer.get_index()

    def build(self, force: bool = False) -> Any:
        data = self._load_clean_data()
        return self._indexer.build_index(data, force_rebuild=force)

    def status(self) -> Dict[str, Any]:
        return self._indexer.get_index_info()


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
    ) -> Dict[str, Any]:
        return await self._engine.aanswer(
            query=query,
            top_k=top_k,
            return_sources=include_sources,
        )

    def stream_answer(self, query: str, top_k: int, include_sources: bool):
        return self._engine.astream_answer(
            query=query,
            top_k=top_k,
            return_sources=include_sources,
        )

    def search(
        self,
        query: str,
        top_k: int,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = self._engine.retriever.retrieve_as_dict(query, top_k=top_k)
        if category:
            results = [
                item
                for item in results
                if category in item.get("category", "")
                or category in item.get("section", "")
            ]
        return results[:top_k]
