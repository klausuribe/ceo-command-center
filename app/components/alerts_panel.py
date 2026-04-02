"""Alert display panel component."""

import streamlit as st


LEVEL_ICONS = {
    "critical": "🔴",
    "warning": "🟡",
    "info": "🔵",
    "positive": "🟢",
}

LEVEL_STYLES = {
    "critical": "error",
    "warning": "warning",
    "info": "info",
    "positive": "success",
}


def alerts_panel(alerts: list[dict], title: str = "Alertas") -> None:
    """Render a panel of business alerts."""
    if not alerts:
        st.success("Sin alertas activas.")
        return

    st.subheader(f"🚨 {title}")

    for alert in alerts:
        level = alert.get("level", "info")
        icon = LEVEL_ICONS.get(level, "🔵")
        style = LEVEL_STYLES.get(level, "info")

        msg = f"**{alert['title']}**"
        if alert.get("description"):
            msg += f"\n\n{alert['description']}"
        if alert.get("action"):
            msg += f"\n\n➡️ {alert['action']}"
        getattr(st, style)(msg, icon=icon)


def compact_alerts(alerts: list[dict], max_show: int = 5) -> None:
    """Compact alert list for sidebar or small spaces."""
    for alert in alerts[:max_show]:
        icon = LEVEL_ICONS.get(alert.get("level", "info"), "🔵")
        st.markdown(f"{icon} **{alert['title']}**")

    remaining = len(alerts) - max_show
    if remaining > 0:
        st.caption(f"+ {remaining} alertas más")
