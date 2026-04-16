"""KPI cards — custom HTML replacement for st.metric.

Cards follow the Financial Dashboard spec: uppercase muted label, large
tabular value (Fira Code), semantic delta with arrow + color, optional
help text and icon. Delta direction is auto-detected from the raw
`delta_value` when provided; fall back to `delta_color`.
"""

from __future__ import annotations

import html
import re

import streamlit as st

from app.components.icons import icon
from config.settings import DEFAULT_CURRENCY


# ── Formatters ───────────────────────────────────────────────────────────
def format_currency(value: float, prefix: str | None = None) -> str:
    """Format a number as currency with K/M suffix."""
    prefix = prefix or DEFAULT_CURRENCY
    if value is None:
        return "—"
    if abs(value) >= 1_000_000:
        return f"{prefix} {value/1_000_000:,.1f}M"
    elif abs(value) >= 1_000:
        return f"{prefix} {value/1_000:,.1f}K"
    return f"{prefix} {value:,.0f}"


def format_pct(value: float, decimals: int = 1) -> str:
    """Format a number as percentage."""
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}%"


def format_number(value: float) -> str:
    """Format a plain number with commas / K/M suffix."""
    if value is None:
        return "—"
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:,.1f}M"
    return f"{value:,.0f}"


# ── Delta helpers ────────────────────────────────────────────────────────
_DELTA_NUM = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def _infer_delta_sign(delta: str) -> int:
    """Return +1 / 0 / -1 based on the first signed number in ``delta``."""
    if not delta:
        return 0
    m = _DELTA_NUM.search(delta)
    if not m:
        return 0
    try:
        n = float(m.group(0).replace(",", "."))
    except ValueError:
        return 0
    if n > 0:
        return 1
    if n < 0:
        return -1
    return 0


def _delta_classes(
    delta: str | None,
    delta_color: str,
) -> tuple[str, str]:
    """Return (css_class, icon_name) for a delta value.

    ``delta_color``:
        "normal"  — green when number is positive, red when negative
        "inverse" — red when positive, green when negative (for bad-when-high KPIs)
        "off"     — always muted
    """
    if not delta:
        return "ccc-kpi__delta--neutral", ""
    if delta_color == "off":
        return "ccc-kpi__delta--neutral", ""
    sign = _infer_delta_sign(delta)
    if sign == 0:
        return "ccc-kpi__delta--neutral", ""
    if delta_color == "inverse":
        sign = -sign
    if sign > 0:
        return "ccc-kpi__delta--pos", "trend-up"
    return "ccc-kpi__delta--neg", "trend-down"


# ── Rendering ────────────────────────────────────────────────────────────
def kpi_card(
    label: str,
    value: str,
    delta: str | None = None,
    delta_color: str = "normal",
    help_text: str | None = None,
    icon_name: str | None = None,
) -> None:
    """Render a single KPI metric card (HTML)."""
    delta_cls, delta_icon_name = _delta_classes(delta, delta_color)

    header_icon = icon(icon_name, size=16) if icon_name else ""
    delta_icon_html = icon(delta_icon_name, size=13) if delta_icon_name else ""
    delta_html = (
        f'<div class="ccc-kpi__delta {delta_cls}">'
        f'{delta_icon_html}<span>{html.escape(delta)}</span></div>'
        if delta else ""
    )
    help_html = (
        f'<div class="ccc-kpi__help">{html.escape(help_text)}</div>'
        if help_text else ""
    )

    st.markdown(
        f"""
        <div class="ccc-kpi">
            <div class="ccc-kpi__header">
                <span>{html.escape(label)}</span>
                {header_icon}
            </div>
            <div class="ccc-kpi__value">{html.escape(value)}</div>
            {delta_html}
            {help_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(metrics: list[dict], cols: int | None = None) -> None:
    """Render a row of KPI cards.

    Each metric dict accepts: label, value, delta, delta_color, help, icon.
    When ``cols`` is None, it defaults to ``len(metrics)`` (one per column).
    """
    cols = cols or len(metrics)
    columns = st.columns(cols, gap="small")
    for i, m in enumerate(metrics):
        with columns[i % cols]:
            kpi_card(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
                help_text=m.get("help"),
                icon_name=m.get("icon"),
            )


def mini_metric(label: str, value: str, help_text: str | None = None) -> None:
    """Smaller secondary metric — used for ratio rows, sub-KPIs."""
    help_html = (
        f'<div class="ccc-kpi__help">{html.escape(help_text)}</div>'
        if help_text else ""
    )
    st.markdown(
        f"""
        <div class="ccc-kpi" style="min-height:96px;padding:0.85rem 1rem;">
            <div class="ccc-kpi__header"><span>{html.escape(label)}</span></div>
            <div class="ccc-kpi__value" style="font-size:1.35rem;">{html.escape(value)}</div>
            {help_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
