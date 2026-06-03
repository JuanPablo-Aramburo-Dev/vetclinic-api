from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Aplicacion

    app_name: str = Field(default="VetClinic API")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)

    # Seguridad

    secret_key: str = Field(...)
    access_token_expire_minutes: int = Field(default=60)
    algorithm: str = Field(default="HS256")

    # Base de datos

    database_url: str = Field(...)


@lru_cache
def get_settings() -> "Settings":
    """Return cached settings instance."""
    return Settings()
