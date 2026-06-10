"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, computed_field
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
    secret_key: str = Field(..., min_length=32)
    access_token_expire_minutes: int = Field(default=60, gt=0)
    algorithm: str = Field(default="HS256")

    # Base de datos (componentes individuales)
    postgres_user: str = Field(...)
    postgres_password: str = Field(...)
    postgres_db: str = Field(...)
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Build the SQLAlchemy database URL from individual components."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance.

    Using lru_cache ensures we only read .env once per process.
    """
    return Settings()
