import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.app.api.dependencies import get_qa_service
from backend.app.api.schemas.requests import QARequest
from backend.app.api.schemas.responses import QAResponse
from backend.app.application.qa_service import QAService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/qa", response_model=QAResponse)
async def ask_question(
    request: QARequest,
    service: QAService = Depends(get_qa_service),
) -> QAResponse:
    result = await service.answer(
        query=request.query,
        top_k=request.top_k,
        include_sources=True,
    )
    return QAResponse(data=result)


@router.post("/qa/stream")
async def ask_question_stream(
    request: QARequest,
    service: QAService = Depends(get_qa_service),
) -> StreamingResponse:
    async def generate():
        try:
            async for chunk in service.stream_answer(
                query=request.query,
                top_k=request.top_k,
                include_sources=True,
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"
        except Exception:
            logger.exception("Streaming answer failed")
            error = {"type": "error", "message": "流式问答失败"}
            yield f"data: {json.dumps(error, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
