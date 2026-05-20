from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.auth import guard_jwt_secret
from app.core.config import settings
from app.core.healthz import router as healthz_router
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase MVP-1: refuse to start with the dev JWT secret in prod-shape envs.
    guard_jwt_secret()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Phase MVP-5: per-IP rate limiting. The Limiter instance must be attached
# to app.state before SlowAPIMiddleware is added so decorated endpoints can
# resolve `request.app.state.limiter` at call time.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def build_cors_origins() -> list[str]:
    """
    Explicit CORS allowlist.

    The Railway frontend calls the Railway backend directly from the browser.
    Therefore the backend must explicitly allow the frontend public origin.
    """

    origins: list[str] = [
        "https://frontend-production-7e8b1.up.railway.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    configured_origins = getattr(settings, "cors_origins", None)

    if isinstance(configured_origins, str):
        for origin in configured_origins.split(","):
            origin = origin.strip()
            if origin and origin not in origins:
                origins.append(origin)

    elif isinstance(configured_origins, list):
        for origin in configured_origins:
            if isinstance(origin, str):
                origin = origin.strip()
                if origin and origin not in origins:
                    origins.append(origin)

    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase MVP-5: defense-in-depth headers on every response.
app.add_middleware(SecurityHeadersMiddleware)
# Phase MVP-5: rate-limit middleware (enforces the per-endpoint @limiter.limit decorators).
app.add_middleware(SlowAPIMiddleware)


@app.get("/")
async def root():
    return {
        "service": "finrlx-backend",
        "status": "ok",
        "version": settings.app_version,
    }


@app.get("/health")
async def health():
    return {
        "service": "finrlx-backend",
        "status": "ok",
        "version": settings.app_version,
    }


@app.get("/api/health")
async def api_health():
    return {
        "service": "finrlx-backend",
        "status": "ok",
        "version": settings.app_version,
    }


app.include_router(api_router, prefix=settings.api_v1_prefix)
# Phase MVP-7: /healthz deep probe (LB-friendly).
app.include_router(healthz_router)
