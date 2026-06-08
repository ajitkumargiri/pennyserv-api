from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PennyServ API"
    app_version: str = "0.1.0"
    app_env: Literal["local", "staging", "production"] = "local"
    app_debug: bool = False

    api_prefix: str = "/api/v1"
    openapi_url: str = "/openapi.json"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=list)

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pennyserv"
    database_migration_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/pennyserv"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 10

    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = True

    readiness_check_database: bool | None = None
    readiness_check_redis: bool | None = None

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4.1-mini"

    data_platform_base_url: AnyHttpUrl | None = None
    data_platform_api_key: SecretStr | None = None
    data_platform_timeout_seconds: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        case_sensitive=False,
    )

    @property
    def is_docs_enabled(self) -> bool:
        return self.app_env != "production"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_environment_requirements(self) -> "Settings":
        if self.readiness_check_database is None:
            self.readiness_check_database = self.app_env != "local"
        if self.readiness_check_redis is None:
            self.readiness_check_redis = self.app_env != "local"

        if self.app_env in {"staging", "production"}:
            missing: list[str] = []
            if not self.database_url:
                missing.append("DATABASE_URL")
            if not self.database_migration_url:
                missing.append("DATABASE_MIGRATION_URL")
            if not self.redis_url:
                missing.append("REDIS_URL")
            if self.data_platform_base_url is None:
                missing.append("DATA_PLATFORM_BASE_URL")
            if self.data_platform_api_key is None:
                missing.append("DATA_PLATFORM_API_KEY")

            if missing:
                fields = ", ".join(missing)
                raise ValueError(
                    f"Missing required environment variables for {self.app_env}: {fields}"
                )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
