"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.app.api import api_router
from backend.app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info(f"{settings.app_name} API starting in {settings.environment}")
    yield
    logger.info(f"{settings.app_name} API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.app_name} API",
        version="1.0.0",
        description=(
            "Backend API for the CEO Command Center. Exposes analytics, AI "
            "analysis, ETL triggers, and auth. Consumed by the Next.js frontend "
            "and eventually by the legacy Streamlit UI during migration."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()
