"""Liveness and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.schemas.kpis import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        app_name=settings.app_name,
        version="1.0.0",
    )
