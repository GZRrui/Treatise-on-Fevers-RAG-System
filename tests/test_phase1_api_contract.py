import json
from collections.abc import AsyncIterator
from types import SimpleNamespace

import httpx
import pytest

from backend.app.application.qa_service import QAService
from backend.app.application.search_service import SearchService
from backend.app.domain.qa import AnswerResult, StreamEvent, StreamEventType
from backend.app.domain.retrieval import ArticleSource, SearchResult
from backend.app.main import create_app
from backend.services.rag_service import RAGService
from src.qa_engine import QAEngine

SOURCE = ArticleSource(
    id=1,
    standard_id=1,
    chapter="辨太阳病脉证并治上",
    section="太阳病",
    category="太阳病",
    text="太阳之为病，脉浮，头项强痛而恶寒。",
    score=0.9,
)


class ContractEngine:
    def __init__(self, *, fail_stream: bool = False) -> None:
        self.calls: list[dict[str, object]] = []
        self.fail_stream = fail_stream

    async def answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AnswerResult:
        self.calls.append({"method": "answer", "top_k": top_k})
        return AnswerResult(answer="回答", query=query, sources=(SOURCE,))

    async def stream_answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AsyncIterator[StreamEvent]:
        self.calls.append({"method": "stream", "top_k": top_k})
        yield StreamEvent(type=StreamEventType.SOURCES, sources=(SOURCE,))
        if self.fail_stream:
            raise RuntimeError("provider failed")
        yield StreamEvent(type=StreamEventType.CONTENT, content="增量")
        yield StreamEvent(
            type=StreamEventType.END,
            content="增量",
            query=query,
        )

    def search(
        self,
        query: str,
        top_k: int,
        category: str | None = None,
    ) -> SearchResult:
        self.calls.append({"method": "search", "top_k": top_k})
        return SearchResult(query=query, items=(SOURCE,)[:top_k])


class ContractContainer:
    def __init__(self, engine: ContractEngine) -> None:
        self.engine = engine
        self.qa_service = QAService(engine)
        self.search_service = SearchService(engine)
        self.ready = True

    async def initialize(self) -> None:
        return None

    def require_qa_service(self) -> QAService:
        return self.qa_service

    def require_search_service(self) -> SearchService:
        return self.search_service


class FailingAnswerEngine(ContractEngine):
    async def answer(
        self,
        query: str,
        top_k: int,
        include_sources: bool,
    ) -> AnswerResult:
        raise RuntimeError("secret provider detail")


def _events(response_text: str) -> list[dict[str, object]]:
    return [
        json.loads(line.removeprefix("data: "))
        for line in response_text.splitlines()
        if line.startswith("data: ")
    ]


@pytest.mark.asyncio
async def test_http_top_k_reaches_qa_and_search_ports() -> None:
    engine = ContractEngine()
    app = create_app(ContractContainer(engine))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        qa_response = await client.post(
            "/api/v1/qa", json={"query": "太阳病", "top_k": 7}
        )
        search_response = await client.post(
            "/api/v1/search", json={"query": "桂枝汤", "top_k": 3}
        )

    assert qa_response.status_code == 200
    assert search_response.status_code == 200
    assert {"method": "answer", "top_k": 7} in engine.calls
    assert {"method": "search", "top_k": 3} in engine.calls
    assert search_response.json()["data"]["total"] <= 3


@pytest.mark.asyncio
async def test_successful_sse_has_deltas_and_exactly_one_end_event() -> None:
    engine = ContractEngine()
    app = create_app(ContractContainer(engine))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/qa/stream", json={"query": "太阳病", "top_k": 2}
        )

    events = _events(response.text)
    assert [event["type"] for event in events] == ["sources", "content", "end"]
    assert sum(event["type"] == "end" for event in events) == 1


@pytest.mark.asyncio
async def test_failed_sse_has_error_without_success_end() -> None:
    engine = ContractEngine(fail_stream=True)
    app = create_app(ContractContainer(engine))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/qa/stream", json={"query": "太阳病", "top_k": 2}
        )

    event_types = [event["type"] for event in _events(response.text)]
    assert event_types == ["sources", "error"]
    assert "end" not in event_types


@pytest.mark.asyncio
async def test_validation_errors_use_stable_envelope() -> None:
    app = create_app(ContractContainer(ContractEngine()))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/search", json={"query": "", "top_k": 0}
        )

    assert response.status_code == 422
    assert response.json() == {
        "code": "VALIDATION_ERROR",
        "message": "请求参数无效",
        "detail": None,
    }


@pytest.mark.asyncio
async def test_internal_errors_use_redacted_stable_envelope() -> None:
    app = create_app(ContractContainer(FailingAnswerEngine()))
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/qa", json={"query": "太阳病", "top_k": 2}
        )

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "服务器内部错误",
        "detail": None,
    }
    assert "secret provider detail" not in response.text


class EmptyIndexProxy:
    _loader = object()

    def retrieve(
        self,
        query: str,
        top_k: int,
        similarity_threshold: float,
    ) -> list[dict[str, object]]:
        return []


class ClosableCumulativeStream:
    def __init__(self) -> None:
        self._chunks = iter(("你", "你好"))
        self.closed = False

    def __aiter__(self) -> "ClosableCumulativeStream":
        return self

    async def __anext__(self) -> object:
        try:
            content = next(self._chunks)
        except StopIteration as exc:
            raise StopAsyncIteration from exc
        return SimpleNamespace(
            delta=None,
            message=SimpleNamespace(content=content),
        )

    async def aclose(self) -> None:
        self.closed = True


class CumulativeLLM:
    def __init__(self) -> None:
        self.stream = ClosableCumulativeStream()

    async def astream_chat(self, messages: object) -> ClosableCumulativeStream:
        return self.stream


@pytest.mark.asyncio
async def test_qa_engine_converts_cumulative_chunks_and_closes_stream() -> None:
    llm = CumulativeLLM()
    engine = QAEngine(index=EmptyIndexProxy(), llm=llm)

    events = [event async for event in engine.astream_answer("测试")]

    content = [event["data"] for event in events if event["type"] == "content"]
    assert content == ["你", "好"]
    assert llm.stream.closed is True


@pytest.mark.asyncio
async def test_qa_engine_closes_provider_stream_when_consumer_disconnects() -> None:
    llm = CumulativeLLM()
    engine = QAEngine(index=EmptyIndexProxy(), llm=llm)
    events = engine.astream_answer("测试")

    assert (await anext(events))["type"] == "sources"
    assert (await anext(events))["type"] == "content"
    await events.aclose()

    assert llm.stream.closed is True


class LegacyRetriever:
    def retrieve_as_dict(
        self,
        query: str,
        top_k: int,
    ) -> list[dict[str, object]]:
        return [
            {
                "id": SOURCE.id,
                "standard_id": SOURCE.standard_id,
                "chapter": SOURCE.chapter,
                "section": SOURCE.section,
                "category": SOURCE.category,
                "text": SOURCE.text,
                "score": SOURCE.score,
                "formulas": [],
            }
        ][:top_k]


class LegacyEngine:
    retriever = LegacyRetriever()

    async def aanswer(
        self,
        query: str,
        top_k: int,
        return_sources: bool,
    ) -> dict[str, object]:
        return {
            "answer": "回答",
            "query": query,
            "sources": self.retriever.retrieve_as_dict(query, top_k),
        }

    async def astream_answer(
        self,
        query: str,
        top_k: int,
        return_sources: bool,
    ) -> AsyncIterator[dict[str, object]]:
        yield {
            "type": "sources",
            "data": self.retriever.retrieve_as_dict(query, top_k),
        }
        yield {"type": "content", "data": "回答"}
        yield {"type": "done", "data": "回答", "query": query}


@pytest.mark.asyncio
async def test_legacy_rag_service_preserves_dict_and_list_contracts() -> None:
    service = RAGService(LegacyEngine())  # type: ignore[arg-type]

    answer = await service.answer("太阳病", top_k=1)
    search = service.search("太阳病", top_k=1)
    events = [event async for event in service.stream_answer("太阳病", top_k=1)]

    assert answer["answer"] == "回答"
    assert isinstance(answer["sources"], list)
    assert isinstance(search, list)
    assert [event["type"] for event in events] == ["sources", "content", "done"]
