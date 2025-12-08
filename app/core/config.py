"""Application configuration and settings helpers."""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Environment-driven configuration for the app."""

    app_name: str = Field(default="VulcanConnect Onshape Configurator")
    environment: str = Field(default="development")
    onshape_base_url: str = Field(
        default="https://cad.onshape.com", description="Base URL for the Onshape instance"
    )
    onshape_access_key: str | None = Field(
        default=None, description="Onshape access key for API authentication"
    )
    onshape_secret_key: str | None = Field(
        default=None, description="Onshape secret key for API authentication"
    )
    request_timeout_seconds: int = Field(default=10)

    class Config:
        env_prefix = "ONSHAPE_"
        env_file = ".env"


@lru_cache

def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
