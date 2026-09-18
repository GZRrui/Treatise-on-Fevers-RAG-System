import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.app.api.dependencies import get_qa_service
from backend.app.api.schemas.requests import QARequest
from backend.app.api.schemas.responses import QAResponse
from backend.app.application.qa_service import QAService
from backend.app.domain.qa import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/qa", response_model=QAResponse)
async def ask_question(
    request: QARequest,
    service: Annotated[QAService, Depends(get_qa_service)],
) -> QAResponse:
    result = await service.answer(
        query=request.query,
        top_k=request.top_k,
        include_sources=True,
    )
    return QAResponse.from_domain(result)


@router.post("/qa/stream")
async def ask_question_stream(
    request: QARequest,
    service: Annotated[QAService, Depends(get_qa_service)],
) -> StreamingResponse:
    async def generate() -> AsyncIterator[str]:
        events = service.stream_answer(
            query=request.query,
            top_k=request.top_k,
            include_sources=True,
        )
        try:
            async for event in events:
                yield _encode_event(event)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Streaming answer failed")
            error = {"type": "error", "message": "流式问答失败"}
            yield f"data: {json.dumps(error, ensure_ascii=False)}\n\n"
        finally:
            close = getattr(events, "aclose", None)
            if close is not None:
                await close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _encode_event(event: StreamEvent) -> str:
    payload: dict[str, object]
    if event.type is StreamEventType.SOURCES:
        payload = {
            "type": event.type.value,
            "data": [
                {
                    "id": item.id,
                    "standard_id": item.standard_id,
                    "chapter": item.chapter,
                    "section": item.section,
                    "category": item.category,
                    "text": item.text,
                    "score": item.score,
                    "formulas": list(item.formulas),
                }
                for item in event.sources
            ],
            "source_count": len(event.sources),
        }
    elif event.type is StreamEventType.CONTENT:
        payload = {"type": event.type.value, "data": event.content}
    elif event.type is StreamEventType.END:
        payload = {
            "type": event.type.value,
            "data": event.content,
            "query": event.query,
        }
    else:
        payload = {"type": event.type.value, "message": event.message}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
