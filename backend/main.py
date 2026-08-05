"""Compatibility entry point for existing deployment commands."""

from backend.app.main import app, create_app, lifespan


def get_qa_engine():
    return app.state.container.qa_engine


# 直接运行入口
if __name__ == "__main__":
    import uvicorn

    from backend.app.config import get_settings

    settings = get_settings()

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
