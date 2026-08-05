"""Backend package."""

__all__ = ["app", "get_qa_engine"]


def __getattr__(name: str):
    if name == "app":
        from backend.main import app

        return app
    if name == "get_qa_engine":
        from backend.main import get_qa_engine

        return get_qa_engine
    raise AttributeError(name)
