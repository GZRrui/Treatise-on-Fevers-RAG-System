import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routers import health, index, qa, search
from backend.app.config import get_settings
from backend.app.container import ApplicationContainer
from backend.app.domain.errors import ApplicationNotReadyError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container: ApplicationContainer = app.state.container
    logger.info("Starting Shanghanlun RAG service")
    await container.initialize()
    try:
        yield
    finally:
        logger.info("Stopping Shanghanlun RAG service")


def create_app(container: ApplicationContainer | None = None) -> FastAPI:
    settings = get_settings()
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    application = FastAPI(
        title=settings.app_name,
        description="《伤寒论》智能问答系统后端 API。",
        version=settings.app_version,
        lifespan=lifespan,
    )
    application.state.container = container or ApplicationContainer()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    application.include_router(health.router, tags=["健康检查"])
    application.include_router(qa.router, prefix="/api/v1", tags=["问答"])
    application.include_router(search.router, prefix="/api/v1", tags=["检索"])
    application.include_router(index.router, prefix="/api/v1", tags=["索引管理"])

    @application.exception_handler(ApplicationNotReadyError)
    async def not_ready_handler(
        request: Request,
        exc: ApplicationNotReadyError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "code": "APPLICATION_NOT_READY",
                "message": "服务尚未准备完成",
                "detail": str(exc) if settings.debug else None,
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "请求参数无效",
                "detail": exc.errors() if settings.debug else None,
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled request error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误",
                "detail": str(exc) if settings.debug else None,
            },
        )

    return application


app = create_app()
