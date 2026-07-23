from pydantic import AliasChoices, Field
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
    # LEAP F1 (D23): when true, ingest requests for source="yfinance" are
    # transparently served by the provider chain (yfinance->stooq->cache).
    leap_price_chain: bool = False
    # LEAP S9 (D16): sourced "why this matters" news annotations. OFF until an
    # LLM provider is configured and the canary passes per batch.
    insights_annotations: bool = False
    # LEAP A2 (D43): Finnhub social-sentiment endpoint requires a paid tier
    # (unverified — E8); the scored social lane activates only with this flag.
    finnhub_premium: bool = False

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
    feature_operator_console: bool = False  # Phase O-0: single-operator LLM workbench. OFF by default; opt-in per env.
    # Phase 16: research fundamentals + peers. Independent flags because the
    # operator may want to gate them separately (fundamentals could ship live
    # while peers wait on a paid-tier upgrade).
    feature_research_fundamentals_ui: bool = True
    feature_research_peers_ui: bool = True
    # Desk W1 (SPEC-01 DEC-7): the Unified Research Desk v2 ships dark.
    # Default OFF; flipped only after the W1 exit gate (SPEC-04 G-1..G-7).
    feature_desk_v2: bool = False
    # Model-lab dashboard: a dedicated tab comparing the walk-forward model
    # tournament (heuristic/ML + RL agents where an artifact exists) and
    # producing one honest research verdict. Default OFF until verified.
    feature_model_lab: bool = False
    # SPEC-05 EP-1 / US-DPK-01..03: the canonical DecisionPacket read-only
    # projection + truth gate. Ships dark. Rollback = drop back to the legacy
    # recommendation read while retaining any new records. Enabling this flag
    # exposes packet *evidence state* only; it never enables alerts, live
    # trading, notifications, or broker execution.
    feature_decision_packet_v1: bool = False

    # LLM provider abstraction (Phase O-5 → 17.4). Two activation modes:
    #
    #   (a) Single provider: set `llm_provider` to one of
    #       "anthropic" | "openai" | "gemini" | "local" and the
    #       matching API key. Empty keeps every assistant endpoint
    #       at 503 (intended state for the zero-token operator phase).
    #
    #   (b) Cascading chain (Phase 17.4): set `llm_provider_chain`
    #       to a comma-separated list, e.g. "gemini,anthropic".
    #       The analyze layer tries each in order, falling back to the
    #       next on StubProviderError (auth failure, rate-limit, empty
    #       response, etc.). Used to put a free provider in front of a
    #       paid one so the paid budget is preserved for genuine
    #       fallback cases.
    #
    # Either mode works; if both are set, `llm_provider_chain` wins.
    llm_provider: str = ""        # "" | "anthropic" | "openai" | "gemini" | "local"
    llm_provider_chain: str = ""  # comma-separated, e.g. "gemini,anthropic"
    llm_model: str = ""           # provider picks a sensible default when empty
    llm_anthropic_api_key: str = ""
    llm_openai_api_key: str = ""
    llm_gemini_api_key: str = ""
    llm_local_base_url: str = "http://localhost:11434"

    # Phase 17 — Research documents (PDF uploads + LLM analysis).
    # Uploads land on a host filesystem path. Locally this is relative;
    # production sets this to a Railway volume mount (e.g.
    # /data/finrlx_documents). The directory is created on first
    # upload if missing.
    documents_storage_path: str = "./_finrlx_documents"
    # Hard size cap per upload — bigger PDFs are rejected at the
    # multipart layer so we don't burn memory on extraction. 50 MB
    # comfortably accommodates most 10-Q / 10-K filings.
    documents_max_size_mb: int = 50

    # Phase 17.1 — Monthly LLM token budget (input + output, summed
    # across providers). The analyze endpoint pre-estimates the call
    # cost and refuses with 503 when current-month usage would exceed
    # this cap. 10M tokens / month is generous for an operator-grade
    # tool; tune per Anthropic billing tolerance. Resets on the first
    # of each month (the budget tracker reads the current year/month
    # bucket only — no manual reset needed).
    max_monthly_llm_tokens: int = 10_000_000

    # Phase 16 — Fundamentals + Peers provider abstraction. Empty
    # `fundamentals_provider` means the stub provider is used (endpoints
    # respond with a structurally-complete envelope tagged source="stub";
    # the frontend renders the "configure provider" empty state).
    # Set fundamentals_provider="finnhub" + the API key below to activate
    # the real surface (real HTTP impl lands in Phase 16.2).
    fundamentals_provider: str = ""  # "" | "stub" | "finnhub"
    # AliasChoices accepts both the conventional Finnhub-SDK env var
    # name (FINNHUB_API_KEY) and the Pydantic-default field-derived name
    # (FUNDAMENTALS_FINNHUB_API_KEY). Operators using either pattern see
    # the key picked up. Documentation recommends FINNHUB_API_KEY for
    # parity with the upstream Finnhub SDK conventions.
    fundamentals_finnhub_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "FINNHUB_API_KEY",
            "FUNDAMENTALS_FINNHUB_API_KEY",
            "fundamentals_finnhub_api_key",
        ),
    )

    # Phase 18 — SEC EDGAR auto-ingest of quarterly filings.
    # SEC requires a User-Agent header on every API request, formatted
    # "AppName operator@example.com" (their fair-access policy). Missing
    # or generic User-Agent strings get throttled or blocked. The
    # resolver and downstream EDGAR services refuse to make the network
    # call when this is empty so operators don't accidentally trigger
    # an SEC block.
    sec_user_agent: str = ""
    # In-process cache TTL for SEC's ticker-to-CIK table. The table
    # changes very rarely (new IPOs, ticker changes), so a weekly
    # refresh is plenty and keeps SEC traffic minimal.
    sec_ticker_cache_ttl_seconds: int = 7 * 24 * 60 * 60  # 7 days

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

    # Google OAuth (sign-in with Gmail). Empty client_id disables the
    # /auth/google/* endpoints (they return 503), so the feature stays
    # invisible to the FE until the operator provisions a Google Cloud
    # OAuth client. See DOCS/handoff/PHASE_OAUTH_GOOGLE_SETUP.md.
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    # Backend callback URI registered in Google Cloud Console. Defaults to
    # the local dev port; override via env in production.
    google_oauth_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    # Frontend URL the user is sent back to after a successful exchange.
    # The backend issues our own tokens and embeds them as URL fragments
    # so localStorage is the only place that ever sees the access token.
    google_oauth_post_login_redirect: str = "http://localhost:3000/login/google-finish"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
