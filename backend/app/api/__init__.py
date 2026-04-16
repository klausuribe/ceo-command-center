"""API router aggregator."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.routes import auth, health, kpis


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(kpis.router)
