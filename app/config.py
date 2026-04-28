"""Application settings loaded from environment variables."""

import warnings
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me-please-use-32-chars-minimum!!"


class Settings(BaseSettings):
    """Runtime configuration for the chat API."""

    environment: Literal["development", "production"] = "development"
    app_name: str = "Chat API"

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/pi_chat"
    test_database_url: str | None = "sqlite+aiosqlite:///./.pytest/test.db"

    jwt_secret_key: str = Field(default=DEFAULT_JWT_SECRET, min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    openrouter_api_key: str | None = None
    openrouter_model: str = "meta-llama/llama-3.2-3b-instruct:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_secret(self) -> "Settings":
        """Reject the default JWT secret in production and warn in development."""
        if self.environment == "production" and self.jwt_secret_key == DEFAULT_JWT_SECRET:
            raise ValueError("JWT_SECRET_KEY must be replaced in production")
        if self.jwt_secret_key == DEFAULT_JWT_SECRET:
            warnings.warn(
                "JWT_SECRET_KEY uses the default development value. Replace it before deployment.",
                stacklevel=2,
            )
        return self

    @model_validator(mode="before")
    @classmethod
    def empty_strings_to_none(cls, values: dict[str, object]) -> dict[str, object]:
        """Treat empty environment values as missing."""
        for key in ("openrouter_api_key", "test_database_url"):
            value = values.get(key)
            if isinstance(value, str) and not value.strip():
                values[key] = None
        return values


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
