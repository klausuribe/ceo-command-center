"""Global sidebar — grouped navigation, filters, SVG icons."""

import calendar
from datetime import date
from typing import Optional

import streamlit as st
from config.settings import APP_NAME, COMPANY_NAME
from database.db_manager import query_scalar

from app.components.icons import icon


# Navigation structure (label, path, icon_name), grouped into sections.
_NAV_GROUPS = [
    ("General", [
        ("Resumen Ejecutivo",  "Home.py",                         "home"),
    ]),
    ("Operación", [
        ("Ventas",             "pages/1_Ventas.py",               "sales"),
        ("Cuentas por Cobrar", "pages/2_Cuentas_por_Cobrar.py",   "receivable"),
        ("Cuentas por Pagar",  "pages/3_Cuentas_por_Pagar.py",    "payable"),
        ("Inventarios",        "pages/4_Inventarios.py",          "inventory"),
        ("Gastos",             "pages/5_Gastos.py",               "expenses"),
    ]),
    ("Finanzas", [
        ("Financiero",         "pages/6_Financiero.py",           "financial"),
        ("Flujo de Caja",      "pages/7_Flujo_de_Caja.py",        "cashflow"),
    ]),
    ("Inteligencia", [
        ("Chat IA",            "pages/8_AI_Chat.py",              "ai"),
        ("Importar Datos",     "pages/9_Importar_Datos.py",       "import"),
    ]),
]


def _latest_period_with_data() -> Optional[str]:
    """Return the most recent period (YYYY-MM) that has data in fact_sales."""
    return query_scalar(
        "SELECT MAX(substr(date_id,1,7)) FROM fact_sales"
    )


def _render_nav() -> None:
    """Render the grouped navigation block."""
    for group_name, items in _NAV_GROUPS:
        st.markdown(
            f'<div class="ccc-sidebar-group">{group_name}</div>',
            unsafe_allow_html=True,
        )
        for label, path, icon_name in items:
            # Streamlit's page_link doesn't support HTML — so we prefix
            # with a Unicode bullet and rely on page_link icon param.
            # We pass icon=None (no emoji) and use plain label.
            st.page_link(path, label=label)


def render_sidebar() -> dict:
    """Render the global sidebar and return selected filters."""
    with st.sidebar:
        # Brand
        st.markdown(
            f'<div class="ccc-sidebar-brand">{icon("bolt", size=20)}'
            f'<span>{APP_NAME}</span></div>'
            f'<div class="ccc-sidebar-brand__sub">{COMPANY_NAME}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        _render_nav()

        st.markdown(
            '<div class="ccc-sidebar-group" style="margin-top:1.3rem;">Filtros</div>',
            unsafe_allow_html=True,
        )

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

        if "sidebar_period" not in st.session_state:
            latest = _latest_period_with_data()
            st.session_state.sidebar_period = (
                latest if latest and latest in periods else periods[0]
            )
        if "sidebar_comparison" not in st.session_state:
            st.session_state.sidebar_comparison = "Mes anterior"
        if "sidebar_day" not in st.session_state:
            st.session_state.sidebar_day = "Todo el mes"

        period = st.selectbox("Período", periods, key="sidebar_period")

        y_sel, m_sel = int(period[:4]), int(period[5:])
        max_day = calendar.monthrange(y_sel, m_sel)[1]
        day_options = ["Todo el mes"] + [str(d) for d in range(1, max_day + 1)]

        if (st.session_state.sidebar_day != "Todo el mes"
                and st.session_state.sidebar_day not in day_options):
            st.session_state.sidebar_day = "Todo el mes"

        day_selection = st.selectbox("Día", day_options, key="sidebar_day")

        if day_selection == "Todo el mes":
            date_prefix = period
            day = None
        else:
            day = int(day_selection)
            date_prefix = f"{period}-{day:02d}"

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

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        if st.button("Refrescar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown(
            '<div style="margin-top:0.75rem;color:var(--ccc-text-subtle);'
            'font-size:0.72rem;display:flex;align-items:center;gap:0.35rem;">'
            f'{icon("sparkles", size=12)}<span>Powered by Claude AI</span></div>',
            unsafe_allow_html=True,
        )

        return {
            "period": period,
            "date_prefix": date_prefix,
            "comparison_period": comp_period,
            "day": day,
        }
