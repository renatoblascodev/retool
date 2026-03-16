from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ToolStack AI API"
    environment: str = "development"
    api_v1_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:5173"]
    database_url: str = (
        "postgresql+asyncpg://toolstack:"
        "toolstack_secret@localhost:5432/toolstack"
    )
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    datasource_encryption_key: str | None = None
    ssrf_allow_hosts: list[str] = []
    # SMTP (optional — if smtp_host is empty, emails are logged to console)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "noreply@toolstack.dev"
    # Frontend URL for invite links
    frontend_url: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
