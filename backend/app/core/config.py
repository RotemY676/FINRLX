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

    # Feature flags (Phase MVP-4) — frontend reads via /api/v1/features.
    # Defaults: ON for backward compat in tests; production overrides to OFF via env.
    feature_research_lane: bool = True   # Show admin/research/RL UI
    feature_paper_trading: bool = True    # Paper portfolio surface
    feature_backtests: bool = True        # Backtest surface
    feature_replay: bool = True           # Replay surface
    feature_universe_ui: bool = True      # Universe workspace surface (Phase A1)
    feature_ops_ui: bool = True           # Ops command center surface (Phase A2)
    feature_policy_ui: bool = True        # Policy Editor surface (Phase A3)
    feature_integrations_ui: bool = True  # Integrations surface (Phase A4)
    feature_risk_ui: bool = True          # Risk workspace surface (Phase B1)
    feature_news_ui: bool = True          # News intelligence surface (Phase B2)

    # Rate limiting (Phase MVP-5) — slowapi token-bucket per remote IP.
    # The global default is generous (covers normal browsing); endpoint-specific
    # decorators tighten the cost on auth + write-heavy paths. Tests disable
    # the limiter by setting rate_limit_enabled=False to keep the suite hermetic.
    rate_limit_enabled: bool = True
    rate_limit_default: str = "120/minute"
    rate_limit_auth: str = "10/minute"
    rate_limit_ingest: str = "20/minute"
    rate_limit_recommendation_write: str = "30/minute"

    # Observability (Phase MVP-7). When dsn is empty, the SDK initializer is
    # a no-op — local dev + CI never reach Sentry. Set SENTRY_DSN in Railway
    # to turn it on in production. `environment` is also logged so prod and
    # preview deploys are separable in the Sentry UI.
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.0  # 0 = no perf tracing in MVP

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
