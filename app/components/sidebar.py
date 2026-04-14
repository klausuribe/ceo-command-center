"""Global sidebar with navigation and filters."""

import calendar
from datetime import date
from typing import Optional

import streamlit as st
from config.settings import APP_NAME, COMPANY_NAME
from database.db_manager import query_scalar


def _latest_period_with_data() -> Optional[str]:
    """Return the most recent period (YYYY-MM) that has data in fact_sales."""
    return query_scalar(
        "SELECT MAX(substr(date_id,1,7)) FROM fact_sales"
    )


def render_sidebar() -> dict:
    """Render the global sidebar and return selected filters.

    Returns dict with:
        period: str            — always YYYY-MM (safe for financial queries)
        date_prefix: str       — YYYY-MM or YYYY-MM-DD (for LIKE queries)
        comparison_period: str — YYYY-MM
        day: int | None        — selected day or None for whole month
    """
    with st.sidebar:
        st.title(f"📊 {APP_NAME}")
        st.caption(COMPANY_NAME)
        st.divider()

        # Navigation
        st.markdown("### Navegación")
        st.page_link("Home.py", label="🏠 Resumen Ejecutivo")
        st.page_link("pages/1_Ventas.py", label="💰 Ventas")
        st.page_link("pages/2_Cuentas_por_Cobrar.py", label="📥 Cuentas por Cobrar")
        st.page_link("pages/3_Cuentas_por_Pagar.py", label="📤 Cuentas por Pagar")
        st.page_link("pages/4_Inventarios.py", label="📦 Inventarios")
        st.page_link("pages/5_Gastos.py", label="💸 Gastos")
        st.page_link("pages/6_Financiero.py", label="📈 Financiero")
        st.page_link("pages/7_Flujo_de_Caja.py", label="🏦 Flujo de Caja")
        st.page_link("pages/8_AI_Chat.py", label="🤖 Chat IA")
        st.page_link("pages/9_Importar_Datos.py", label="📥 Importar Datos")
        st.divider()

        # ── Period filters ──────────────────────────────────────────
        st.markdown("### Filtros")
        today = date.today()

        # Build list of available periods (last 24 months)
        periods = []
        for offset in range(24):
            m = today.month - offset
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            periods.append(f"{y}-{m:02d}")

        # Set session_state defaults BEFORE creating widgets.
        # The key param on each widget reads/writes session_state automatically.
        # We only set the default once (first visit).
        if "sidebar_period" not in st.session_state:
            latest = _latest_period_with_data()
            if latest and latest in periods:
                st.session_state.sidebar_period = latest
            else:
                st.session_state.sidebar_period = periods[0]

        if "sidebar_comparison" not in st.session_state:
            st.session_state.sidebar_comparison = "Mes anterior"

        if "sidebar_day" not in st.session_state:
            st.session_state.sidebar_day = "Todo el mes"

        # Month selector — key alone handles persistence, no index param
        period = st.selectbox("Período", periods, key="sidebar_period")

        # Day selector within selected month
        y_sel, m_sel = int(period[:4]), int(period[5:])
        max_day = calendar.monthrange(y_sel, m_sel)[1]
        day_options = ["Todo el mes"] + [str(d) for d in range(1, max_day + 1)]

        # Reset day if it exceeds the new month's range
        if (st.session_state.sidebar_day != "Todo el mes"
                and st.session_state.sidebar_day not in day_options):
            st.session_state.sidebar_day = "Todo el mes"

        day_selection = st.selectbox("Día", day_options, key="sidebar_day")

        # Build date_prefix: YYYY-MM or YYYY-MM-DD
        if day_selection == "Todo el mes":
            date_prefix = period
            day = None
        else:
            day = int(day_selection)
            date_prefix = f"{period}-{day:02d}"

        # Comparison period
        comparison = st.selectbox(
            "Comparar con",
            ["Mes anterior", "Mismo mes año pasado"],
            key="sidebar_comparison",
        )

        if comparison == "Mes anterior":
            if m_sel == 1:
                comp_period = f"{y_sel-1}-12"
            else:
                comp_period = f"{y_sel}-{m_sel-1:02d}"
        else:
            comp_period = f"{y_sel-1}-{period[5:]}"

        st.divider()

        # Cache controls
        if st.button("🔄 Refrescar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.caption("Powered by Claude AI")

        return {
            "period": period,
            "date_prefix": date_prefix,
            "comparison_period": comp_period,
            "day": day,
        }
