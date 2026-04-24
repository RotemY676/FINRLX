from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


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