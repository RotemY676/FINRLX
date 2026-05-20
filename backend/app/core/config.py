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

    # Auth (Phase MVP-1)
    # JWT secret MUST be overridden via JWT_SECRET env var in production.
    # The default below is used only for local dev + tests; it is rejected at startup
    # if running under non-debug + non-sqlite (see app.core.auth.guard_jwt_secret).
    jwt_secret: str = "dev-only-not-for-production-jwt-secret-rotate-me-please"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    bcrypt_rounds: int = 12  # ~250ms on commodity hardware
    # Signup gating: when True, only emails present in email_allowlist may sign up
    require_email_allowlist: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
