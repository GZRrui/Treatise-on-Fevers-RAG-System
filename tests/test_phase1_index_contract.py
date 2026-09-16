from pathlib import Path

import httpx
import pytest
from llama_index.core.embeddings import MockEmbedding

from backend.app.application.index_service import IndexService
from backend.app.container import ApplicationContainer
from backend.app.domain.indexing import IndexState, IndexStatus
from backend.app.main import create_app
from src.indexer import Indexer


class MissingIndexReader:
    def __init__(self) -> None:
        self.load_calls = 0

    def load_existing(self) -> object:
        self.load_calls += 1
        raise FileNotFoundError("no persisted index")

    def status(self) -> IndexStatus:
        return IndexStatus(state=IndexState.MISSING)


@pytest.mark.asyncio
async def test_empty_index_starts_not_ready_without_building() -> None:
    reader = MissingIndexReader()
    container = ApplicationContainer(IndexService(reader))

    await container.initialize()

    assert reader.load_calls == 1
    assert container.ready is False
    assert container.index_service is not None
    assert container.index_service.current_index is None


@pytest.mark.asyncio
async def test_index_http_surface_is_read_only() -> None:
    reader = MissingIndexReader()
    container = ApplicationContainer(IndexService(reader))
    await container.initialize()
    app = create_app(container)

    assert "/api/v1/index/build" not in app.openapi()["paths"]

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        status_response = await client.get("/api/v1/index/status")
        ready_response = await client.get("/health/ready")
        build_response = await client.post("/api/v1/index/build", json={})
        qa_response = await client.post(
            "/api/v1/qa",
            json={"query": "太阳病", "top_k": 2},
        )

    assert status_response.status_code == 200
    assert status_response.json() == {
        "exists": False,
        "vector_count": 0,
        "storage_path": "",
        "embedding_model": "",
        "embedding_dim": 0,
        "status": "missing",
    }
    assert ready_response.status_code == 503
    assert ready_response.json()["status"] == "not_ready"
    assert build_response.status_code == 404
    assert qa_response.status_code == 503
    assert qa_response.json() == {
        "code": "APPLICATION_NOT_READY",
        "message": "服务尚未准备完成",
        "detail": None,
    }


def test_indexer_does_not_rebuild_when_persisted_index_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    indexer = Indexer(vector_store_path=str(tmp_path / "vector_store.json"))

    def fail_if_called(*args: object, **kwargs: object) -> object:
        raise AssertionError("API startup must not rebuild an index")

    monkeypatch.setattr(indexer, "build_index", fail_if_called)

    with pytest.raises(FileNotFoundError):
        indexer.get_index()


def test_indexer_construction_does_not_create_an_llm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> object:
        raise AssertionError("Index construction must not create an LLM")

    monkeypatch.setattr("src.model_factory.create_llm", fail_if_called)

    Indexer(vector_store_path=str(tmp_path / "vector_store.json"))


def test_controlled_cli_build_smoke(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    class FakeLoader:
        def load_clean_data(self) -> list[dict[str, object]]:
            calls.append(("load", None))
            return [{"id": 1}]

    class FakeIndexer:
        def build_index(
            self,
            data: list[dict[str, object]],
            force_rebuild: bool,
        ) -> object:
            calls.append(("build", force_rebuild))
            return object()

        def get_index_info(self) -> dict[str, object]:
            return {"exists": True, "vector_count": 1}

    monkeypatch.setattr("src.data_loader.DataLoader", FakeLoader)
    monkeypatch.setattr("src.indexer.Indexer", FakeIndexer)

    from scripts.build_index import main

    main()

    assert calls == [("load", None), ("build", True)]


def test_existing_index_remains_loadable(tmp_path: Path) -> None:
    path = tmp_path / "index" / "vector_store.json"
    embedding = MockEmbedding(embed_dim=8)
    data = [
        {
            "id": 1,
            "standard_id": 1,
            "chapter": "辨太阳病脉证并治上",
            "section": "太阳病",
            "category": "太阳病",
            "text": "太阳之为病，脉浮，头项强痛而恶寒。",
            "formulas": [],
        }
    ]
    builder = Indexer(
        embedding_model="mock-embedding",
        embedding_dimension=8,
        embedding=embedding,
        vector_store_path=str(path),
    )
    builder.build_index(data, force_rebuild=True)

    reader = Indexer(
        embedding_model="mock-embedding",
        embedding_dimension=8,
        embedding=embedding,
        vector_store_path=str(path),
    )

    assert reader.load_existing_index() is not None
