"""Global sidebar with navigation and filters."""

from datetime import date

import streamlit as st
from config.settings import APP_NAME, COMPANY_NAME


def render_sidebar() -> dict:
    """Render the global sidebar and return selected filters.

    Returns dict with: period, comparison_period
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
        st.divider()

        # Period filters
        st.markdown("### Filtros")
        today = date.today()

        # Build list of available periods
        periods = []
        for offset in range(24):
            m = today.month - offset
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            periods.append(f"{y}-{m:02d}")

        period = st.selectbox("Período", periods, index=0)
        comparison = st.selectbox("Comparar con", ["Mes anterior", "Mismo mes año pasado"], index=0)

        if comparison == "Mes anterior":
            y, m = int(period[:4]), int(period[5:])
            if m == 1:
                comp_period = f"{y-1}-12"
            else:
                comp_period = f"{y}-{m-1:02d}"
        else:
            y = int(period[:4])
            comp_period = f"{y-1}-{period[5:]}"

        st.divider()

        # Cache controls
        if st.button("🔄 Refrescar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.caption("Powered by Claude AI")

        return {"period": period, "comparison_period": comp_period}
