"""KPI endpoints — thin wrappers over the shared analytics layer."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from analytics.kpi_calculator import all_kpis  # type: ignore[import-not-found]

from backend.app.core.deps import get_current_user
from backend.app.core.users import User
from backend.app.schemas.kpis import AllKpisResponse


router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("/all", response_model=AllKpisResponse)
def get_all_kpis(
    period: str | None = Query(
        default=None,
        pattern=r"^\d{4}-\d{2}$",
        description="Target period as YYYY-MM. Defaults to current month.",
    ),
    _: User = Depends(get_current_user),
) -> AllKpisResponse:
    """Compute the full cross-module KPI snapshot used by the Morning Briefing."""
    try:
        snapshot = all_kpis(period)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to compute KPIs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute KPIs",
        ) from exc

    return AllKpisResponse(**snapshot)
