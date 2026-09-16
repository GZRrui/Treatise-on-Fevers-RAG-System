from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from backend.app.application.qa_service import QAService
from backend.app.application.search_service import SearchService
from backend.app.domain.qa import AnswerResult, StreamEvent, StreamEventType
from backend.app.domain.retrieval import SearchResult
from backend.app.main import create_app


class FakeEngine:
    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    async def answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AnswerResult:
        self.calls.append(
            {
                "method": "answer",
                "query": query,
                "top_k": top_k,
                "include_sources": include_sources,
            }
        )
        return AnswerResult(answer="test answer", query=query)

    def stream_answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AsyncIterator[StreamEvent]:
        self.calls.append(
            {
                "method": "stream",
                "query": query,
                "top_k": top_k,
                "include_sources": include_sources,
            }
        )

        async def generate():
            yield StreamEvent(type=StreamEventType.CONTENT, content="test")
            yield StreamEvent(
                type=StreamEventType.END,
                content="test",
                query=query,
            )

        return generate()

    def search(
        self,
        query: str,
        top_k: int,
        category: str | None = None,
    ) -> SearchResult:
        self.calls.append(
            {
                "method": "search",
                "query": query,
                "top_k": top_k,
                "category": category,
            }
        )
        return SearchResult(query=query, items=())


@pytest.mark.asyncio
async def test_qa_service_forwards_use_case_parameters():
    engine = FakeEngine()
    service = QAService(engine)

    result = await service.answer("太阳病", top_k=7, include_sources=False)

    assert result.answer == "test answer"
    assert engine.calls == [
        {
            "method": "answer",
            "query": "太阳病",
            "top_k": 7,
            "include_sources": False,
        }
    ]


def test_search_service_forwards_filters():
    engine = FakeEngine()
    service = SearchService(engine)

    service.search("桂枝汤", top_k=3, category="太阳病")

    assert engine.calls == [
        {
            "method": "search",
            "query": "桂枝汤",
            "top_k": 3,
            "category": "太阳病",
        }
    ]


class FakeIndexService:
    current_index = object()

    def status(self):
        return {
            "exists": True,
            "vector_count": 1,
            "storage_path": "test",
            "embedding_model": "test",
            "embedding_dim": 3,
        }


class FakeContainer:
    def __init__(self):
        engine = FakeEngine()
        self.qa_service = QAService(engine)
        self.search_service = SearchService(engine)
        self.index_service = FakeIndexService()
        self.ready = True

    async def initialize(self):
        return None

    def require_qa_service(self):
        return self.qa_service

    def require_search_service(self):
        return self.search_service

    def require_index_service(self):
        return self.index_service


@pytest.mark.asyncio
async def test_api_routes_use_injected_application_services():
    app = create_app(FakeContainer())
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/qa",
            json={"query": "太阳病", "top_k": 2},
        )
        assert response.status_code == 200
        assert response.json()["data"]["query"] == "太阳病"

        stream_response = await client.post(
            "/api/v1/qa/stream",
            json={"query": "太阳病", "top_k": 2},
        )
        assert stream_response.status_code == 200
        assert '"type": "content"' in stream_response.text


def test_domain_and_application_do_not_import_frameworks():
    from pathlib import Path

    app_root = Path(__file__).parents[1] / "backend" / "app"
    forbidden = ("fastapi", "llama_index", "sqlalchemy", "src.")

    for package in ("domain", "application"):
        for path in (app_root / package).rglob("*.py"):
            content = path.read_text(encoding="utf-8")
            assert not any(name in content for name in forbidden), path
