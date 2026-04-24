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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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