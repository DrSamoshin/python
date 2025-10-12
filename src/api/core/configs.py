import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from src.api.core.logging_config import setup_logging


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Application
    app_title: str = "test_app"
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8080

    # Environment
    env: Literal["dev", "prod"] = "dev"  # Default to test for safety
    log_level: str = "INFO"
    cors_origins: str = ""
    workers: int = 4

    # Database
    @property
    def database_url(self) -> str:
        """Get database URL based on environment."""
        urls = {
            "dev": "postgresql+asyncpg://dev_user:dev_pass@localhost:5432/myapp_dev",
            "prod": os.getenv("DATABASE_URL", ""),
        }
        return urls.get(self.env, urls["dev"])

    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    @property
    def database_echo(self) -> bool:
        """Enable SQL logging in dev only."""
        return self.env == "dev"

    def model_post_init(self, __context):
        setup_logging(self.log_level)

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if
                origin.strip()]


settings = Settings()
