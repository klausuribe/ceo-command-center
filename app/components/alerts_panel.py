"""Alert display panel — side-border cards with SVG icons."""

from __future__ import annotations

import html

import streamlit as st

from app.components.icons import icon


_LEVEL_ICON = {
    "critical": "alert",
    "warning":  "alert-circle",
    "info":     "info",
    "positive": "check",
}


def _alert_html(alert: dict) -> str:
    level = alert.get("level", "info")
    icon_name = _LEVEL_ICON.get(level, "info")
    title = html.escape(str(alert.get("title", "")))
    desc = alert.get("description")
    action = alert.get("action")

    desc_html = f'<div class="ccc-alert__desc">{html.escape(str(desc))}</div>' if desc else ""
    action_html = (
        f'<div class="ccc-alert__action">'
        f'{icon("chevron-right", size=13)}<span>{html.escape(str(action))}</span>'
        f'</div>' if action else ""
    )
    return (
        f'<div class="ccc-alert ccc-alert--{level}">'
        f'<div class="ccc-alert__icon">{icon(icon_name, size=18)}</div>'
        f'<div class="ccc-alert__body">'
        f'<div class="ccc-alert__title">{title}</div>'
        f'{desc_html}{action_html}'
        f'</div></div>'
    )


def alerts_panel(alerts: list[dict], title: str = "Alertas") -> None:
    """Render a panel of business alerts."""
    st.markdown(
        f'<div class="ccc-section-title">{icon("alert", size=16)}'
        f'<span>{html.escape(title)}</span></div>',
        unsafe_allow_html=True,
    )

    if not alerts:
        st.markdown(
            f'<div class="ccc-alert ccc-alert--positive">'
            f'<div class="ccc-alert__icon">{icon("check", size=18)}</div>'
            f'<div class="ccc-alert__body">'
            f'<div class="ccc-alert__title">Sin alertas activas</div>'
            f'<div class="ccc-alert__desc">Todos los indicadores dentro de rango.</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown("".join(_alert_html(a) for a in alerts), unsafe_allow_html=True)


def compact_alerts(alerts: list[dict], max_show: int = 5) -> None:
    """Compact alert list for sidebar or small spaces."""
    if not alerts:
        return
    for alert in alerts[:max_show]:
        level = alert.get("level", "info")
        icon_name = _LEVEL_ICON.get(level, "info")
        color_map = {
            "critical": "var(--ccc-negative)",
            "warning":  "var(--ccc-warning)",
            "info":     "var(--ccc-info)",
            "positive": "var(--ccc-positive)",
        }
        st.markdown(
            f'<div style="display:flex;gap:0.4rem;align-items:center;'
            f'padding:0.25rem 0;color:var(--ccc-text);font-size:0.88rem;">'
            f'<span style="color:{color_map.get(level)}">'
            f'{icon(icon_name, size=14)}</span>'
            f'<span>{html.escape(str(alert["title"]))}</span></div>',
            unsafe_allow_html=True,
        )

    remaining = len(alerts) - max_show
    if remaining > 0:
        st.caption(f"+ {remaining} alertas más")
