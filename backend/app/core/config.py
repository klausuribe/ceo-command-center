"""Backend settings — extends the shared config/settings with web-specific values."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Reuse the shared settings loader so ANTHROPIC_API_KEY, DB_PATH, etc.
# resolve the same way for Streamlit and the API.
from config import settings as shared_settings  # type: ignore[import-not-found]


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class BackendSettings(BaseSettings):
    """FastAPI-specific settings. Shared values come from `config.settings`."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API
    api_prefix: str = "/api"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",  # Next.js dev
            "http://localhost:8501",  # Streamlit dev
            "http://127.0.0.1:3000",
        ]
    )

    # Auth
    jwt_secret_key: str = Field(default=shared_settings.AUTH_SECRET_KEY)
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60 * 8   # 8h workday
    refresh_token_ttl_days: int = 14

    # Shared forwarded values (read-only)
    app_name: str = shared_settings.APP_NAME
    company_name: str = shared_settings.COMPANY_NAME
    default_currency: str = shared_settings.DEFAULT_CURRENCY
    db_path: str = shared_settings.DB_PATH
    anthropic_api_key: str = shared_settings.ANTHROPIC_API_KEY
    environment: str = Field(default="development")


@lru_cache(maxsize=1)
def get_settings() -> BackendSettings:
    """Return a cached BackendSettings instance."""
    return BackendSettings()
