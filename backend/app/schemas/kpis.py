"""Pydantic DTOs for KPI endpoints.

Keeps shapes permissive (dict[str, Any]) during Phase 0 because the analytics
layer already returns tightly-typed Python dicts. A later phase will split each
module into its own strict schema once endpoints stabilize.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AllKpisResponse(BaseModel):
    sales: dict[str, Any] = Field(default_factory=dict)
    receivables: dict[str, Any] = Field(default_factory=dict)
    payables: dict[str, Any] = Field(default_factory=dict)
    inventory: dict[str, Any] = Field(default_factory=dict)
    expenses: dict[str, Any] = Field(default_factory=dict)
    financial: dict[str, Any] = Field(default_factory=dict)
    cashflow: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
    app_name: str
    version: str
