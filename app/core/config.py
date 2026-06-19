from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Order Processing API"
    environment: str = "local"
    debug: bool = True
    log_level: str = "INFO"

    database_url: str = "sqlite:///./app.db"

    secret_key: str = Field(default="change-me-in-local-env", min_length=16)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    backend_cors_origins: list[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def sqlalchemy_connect_args(self) -> dict[str, Any]:
        if self.database_url.startswith("sqlite"):
            return {"check_same_thread": False}
        return {}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
