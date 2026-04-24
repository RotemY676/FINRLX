from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "FINRLX"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database — defaults to SQLite for local dev, use PostgreSQL in production/Docker
    database_url: str = "sqlite+aiosqlite:///./finrlx_dev.db"
    database_echo: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # API
    api_v1_prefix: str = "/api/v1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
