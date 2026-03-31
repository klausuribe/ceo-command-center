"""What-If scenario panel with sliders and real-time impact calculation."""

import streamlit as st
from app.components.kpi_cards import format_currency, format_pct


def whatif_sliders() -> dict:
    """Render what-if scenario sliders and return parameters."""
    st.subheader("🎛️ Parámetros del Escenario")

    col1, col2 = st.columns(2)

    with col1:
        sales_change = st.slider(
            "Variación de Ventas (%)",
            min_value=-50, max_value=50, value=0, step=5,
            help="Cambio porcentual en revenue",
        )
        cost_change = st.slider(
            "Variación de Costos (%)",
            min_value=-30, max_value=30, value=0, step=5,
            help="Cambio porcentual en costo de ventas",
        )
        opex_change = st.slider(
            "Variación Gastos Operativos (%)",
            min_value=-30, max_value=30, value=0, step=5,
        )

    with col2:
        dso_change = st.slider(
            "Cambio en DSO (días)",
            min_value=-30, max_value=60, value=0, step=5,
            help="Días adicionales de cobro",
        )
        investment = st.number_input(
            "Nueva Inversión (Bs)",
            min_value=0, max_value=500000, value=0, step=10000,
            help="Inversión única (salida de caja)",
        )
        fixed_change = st.number_input(
            "Cambio en Gastos Fijos Mensuales (Bs)",
            min_value=-50000, max_value=50000, value=0, step=5000,
        )

    return {
        "sales_change_pct": sales_change,
        "cost_change_pct": cost_change,
        "opex_change_pct": opex_change,
        "dso_change_days": dso_change,
        "new_investment": investment,
        "fixed_expense_change": fixed_change,
    }


def display_results(results: dict) -> None:
    """Display what-if simulation results."""
    base = results["baseline"]
    proj = results["projected"]
    delta = results["delta"]

    st.subheader("📊 Impacto Proyectado")

    # P&L comparison
    st.markdown("#### Estado de Resultados")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Métrica**")
        st.markdown("Revenue")
        st.markdown("Utilidad Bruta")
        st.markdown("Margen Bruto")
        st.markdown("Utilidad Neta")
        st.markdown("Margen Neto")
    with col2:
        st.markdown("**Actual**")
        st.markdown(format_currency(base["revenue"]))
        st.markdown(format_currency(base["gross_profit"]))
        st.markdown(format_pct(base["gross_margin_pct"]))
        st.markdown(format_currency(base["net_income"]))
        st.markdown(format_pct(base["net_margin_pct"]))
    with col3:
        st.markdown("**Proyectado**")
        st.markdown(format_currency(proj["revenue"]))
        st.markdown(format_currency(proj["gross_profit"]))
        st.markdown(format_pct(proj["gross_margin_pct"]))
        st.markdown(format_currency(proj["net_income"]))
        st.markdown(format_pct(proj["net_margin_pct"]))

    st.divider()

    # Cash flow impact
    st.markdown("#### Flujo de Caja")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cash Actual", format_currency(base["cash_balance"]))
    c2.metric("Cash +30d", format_currency(proj["cash_30d"]),
              delta=format_currency(proj["cash_30d"] - base["cash_balance"]))
    c3.metric("Cash +90d", format_currency(proj["cash_90d"]),
              delta=format_currency(proj["cash_90d"] - base["cash_balance"]))

    # Risk indicator
    net_impact = delta["net_income"]
    cash_impact = delta["cash_impact_90d"]

    if net_impact < 0 and cash_impact < -100000:
        st.error(f"🔴 **RIESGO ALTO** — Pérdida de {format_currency(abs(net_impact))} en utilidad "
                 f"y {format_currency(abs(cash_impact))} en caja a 90 días.")
    elif net_impact < 0 or cash_impact < 0:
        st.warning(f"🟡 **RIESGO MEDIO** — Impacto negativo: "
                   f"{format_currency(net_impact)} en utilidad, "
                   f"{format_currency(cash_impact)} en caja.")
    else:
        st.success(f"🟢 **IMPACTO POSITIVO** — +{format_currency(net_impact)} en utilidad, "
                   f"+{format_currency(cash_impact)} en caja a 90 días.")
