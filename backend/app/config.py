"""Runtime configuration contract shared by API and legacy entry points."""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class APISettings(BaseSettings):
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    app_name: str = "《伤寒论》RAG 智能问答系统 API"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    storage_dir: Path = PROJECT_ROOT / "storage"
    data_dir: Path = PROJECT_ROOT / "data"
    vector_store_path: Path | None = None

    dashscope_api_key: str = Field(default="", repr=False)
    dashscope_api_base: str = (
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    rag_offline_mode: bool = True
    embedding_model: str = "text-embedding-v3"
    embedding_dim: int = Field(default=1536, ge=1)
    llm_model: str = "qwen-plus"
    llm_temperature: float = Field(default=0.7, ge=0, le=2)
    llm_max_tokens: int = Field(default=2000, ge=1)
    top_k: int = Field(default=5, ge=1)
    similarity_threshold: float = Field(default=0.7, ge=0, le=1)

    database_url: str = ""
    jwt_secret: str = Field(
        default="dev-secret-change-in-production",
        repr=False,
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = Field(default=24, ge=1)
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_environment_contract(self) -> "APISettings":
        if self.app_env is AppEnvironment.TEST and not self.rag_offline_mode:
            raise ValueError("Test environment must enable RAG_OFFLINE_MODE")
        if self.app_env is AppEnvironment.PRODUCTION:
            self._validate_production()
        return self

    def _validate_production(self) -> None:
        errors: list[str] = []
        if self.debug:
            errors.append("DEBUG must be false")
        if self.rag_offline_mode:
            errors.append("RAG_OFFLINE_MODE must be false")
        if not self.dashscope_api_key or self.dashscope_api_key.startswith("sk-xxxx"):
            errors.append("DASHSCOPE_API_KEY must be configured")
        if not self.database_url:
            errors.append("DATABASE_URL must be configured")
        if len(self.jwt_secret) < 32 or self.jwt_secret.startswith("dev-secret"):
            errors.append("JWT_SECRET must contain at least 32 non-default characters")

        origins = self.cors_origin_list
        if not origins:
            errors.append("CORS_ORIGINS must contain at least one trusted origin")
        for origin in origins:
            parsed = urlparse(origin)
            if (
                origin == "*"
                or parsed.scheme != "https"
                or parsed.hostname in {"localhost", "127.0.0.1", "::1"}
            ):
                errors.append(
                    "CORS_ORIGINS must contain only explicit HTTPS origins"
                )
                break
        if errors:
            raise ValueError("Invalid production configuration: " + "; ".join(errors))

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.storage_dir / 'rag_system.db'}"

    @property
    def resolved_vector_store_path(self) -> Path:
        return self.vector_store_path or self.storage_dir / "vector_store.json"


@lru_cache
def get_settings() -> APISettings:
    return APISettings()
