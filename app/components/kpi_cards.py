"""Reusable KPI card components."""

import streamlit as st


def kpi_card(
    label: str,
    value: str,
    delta: str | None = None,
    delta_color: str = "normal",
    help_text: str | None = None,
) -> None:
    """Render a single KPI metric card."""
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text,
    )


def kpi_row(metrics: list[dict], cols: int = 4) -> None:
    """Render a row of KPI cards.

    Each metric dict: {label, value, delta?, delta_color?, help?}
    """
    columns = st.columns(cols)
    for i, m in enumerate(metrics):
        with columns[i % cols]:
            kpi_card(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
                help_text=m.get("help"),
            )


def format_currency(value: float, prefix: str = "Bs") -> str:
    """Format a number as currency."""
    if abs(value) >= 1_000_000:
        return f"{prefix} {value/1_000_000:,.1f}M"
    elif abs(value) >= 1_000:
        return f"{prefix} {value/1_000:,.1f}K"
    return f"{prefix} {value:,.0f}"


def format_pct(value: float, decimals: int = 1) -> str:
    """Format a number as percentage."""
    return f"{value:,.{decimals}f}%"


def format_number(value: float) -> str:
    """Format a plain number with commas."""
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:,.1f}M"
    return f"{value:,.0f}"
