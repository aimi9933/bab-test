from __future__ import annotations

import base64
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="BACKEND_", case_sensitive=False)

    app_name: str = "LLM Provider Manager"
    database_url: str = Field(default="sqlite:///./backend/data/providers.db")
    api_key_secret: str = Field(default="change-me", description="Secret used to encrypt API keys")
    backup_file: str = Field(default="backend/config_backup.json")
    request_timeout_seconds: float = Field(default=10.0, ge=0.1)
    health_check_enabled: bool = Field(default=True, description="Enable automatic health checks")
    health_check_interval_seconds: float = Field(default=60.0, ge=1.0, description="Interval between health checks in seconds")
    health_check_timeout_seconds: float = Field(default=5.0, ge=0.1, description="Timeout for individual health checks")
    health_check_failure_threshold: int = Field(default=3, ge=1, description="Consecutive failures before marking provider unhealthy")

    def ensure_directories(self) -> None:
        """Create directories for configured paths when necessary."""
        db_url = self.database_url
        if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
            path_str = db_url.replace("sqlite:///", "")
            path = Path(path_str).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
        backup_path = Path(self.backup_file).expanduser().resolve()
        backup_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def backup_path(self) -> Path:
        return Path(self.backup_file).expanduser().resolve()

    @property
    def derived_encryption_key(self) -> bytes:
        digest = hashlib.sha256(self.api_key_secret.encode()).digest()
        return base64.urlsafe_b64encode(digest)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings


def reset_settings_cache() -> None:
    """Clear the cached settings instance (primarily for testing)."""
    get_settings.cache_clear()  # type: ignore[attr-defined]
