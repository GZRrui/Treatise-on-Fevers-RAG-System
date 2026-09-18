from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.config import APISettings, AppEnvironment


def test_test_environment_requires_mock_provider() -> None:
    with pytest.raises(ValidationError, match="RAG_OFFLINE_MODE"):
        APISettings(
            _env_file=None,
            app_env=AppEnvironment.TEST,
            rag_offline_mode=False,
        )


def test_production_rejects_unsafe_defaults() -> None:
    with pytest.raises(ValidationError, match="Invalid production configuration"):
        APISettings(
            _env_file=None,
            app_env=AppEnvironment.PRODUCTION,
            debug=True,
            cors_origins="*",
        )


def test_production_accepts_explicit_secure_configuration(tmp_path: Path) -> None:
    settings = APISettings(
        _env_file=None,
        app_env=AppEnvironment.PRODUCTION,
        rag_offline_mode=False,
        dashscope_api_key="sk-production-secret",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'production.db'}",
        jwt_secret="a" * 32,
        cors_origins="https://rag.example.com",
    )

    assert settings.app_env is AppEnvironment.PRODUCTION
    assert "sk-production-secret" not in repr(settings)
    assert "a" * 32 not in repr(settings)
