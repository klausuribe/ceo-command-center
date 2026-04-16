"""Módulo de Flujo de Caja — Cash Flow Dashboard."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Flujo de Caja — CEO Command Center", page_icon=":bank:", layout="wide")

from app.components.theme import apply_theme
from app.components.auth import require_auth
from app.components.sidebar import render_sidebar
from app.components.page_header import page_header, section_title

apply_theme()
require_auth()
from app.components.kpi_cards import kpi_row, format_currency
from app.components.charts import line_chart, bar_chart, waterfall_chart
from app.components.tables import data_table
from app.components.ai_analysis_box import ai_analysis_box
from analytics.kpi_calculator import cashflow_kpis
from analytics import cashflow_analytics as ca
from ai.engine import get_engine
from ai.prompts.cashflow_prompts import CASHFLOW_ANALYSIS

filters = render_sidebar()
period = filters["period"]
date_prefix = filters["date_prefix"]

page_header("Flujo de Caja", "cashflow",
            subtitle="Saldo, runway, proyecciones y patrón estacional")

try:
    kpis = cashflow_kpis()
    breakeven = ca.breakeven_days()

    kpi_row([
        {"label": "Saldo Actual", "value": format_currency(kpis["current_balance"]),
         "help": "Último saldo registrado en caja",
         "icon": "coins"},
        {"label": "Ingresos del Mes", "value": format_currency(kpis["month_inflow"]),
         "icon": "trend-up"},
        {"label": "Egresos del Mes", "value": format_currency(kpis["month_outflow"]),
         "icon": "trend-down"},
        {"label": "Flujo Neto Diario Prom.", "value": format_currency(kpis["avg_daily_net"]),
         "delta": "Runway: ∞" if kpis["runway_days"] is None else f"Runway: {int(kpis['runway_days'])} días",
         "delta_color": "off",
         "help": "Promedio diario ingresos - egresos (últimos 30 días). Runway = días hasta agotar caja",
         "icon": "bolt"},
    ])

    st.divider()

    # Daily balance + Monthly summary
    col1, col2 = st.columns(2)
    with col1:
        daily = ca.daily_balance(30)
        if not daily.empty:
            line_chart(daily, x="date_id", y="balance",
                       title="Saldo Diario — Últimos 30 Días", y_label="Bs")

    with col2:
        monthly = ca.monthly_summary(12)
        if not monthly.empty:
            monthly = monthly.sort_values("period")
            line_chart(monthly, x="period", y=["inflow", "outflow", "net_flow"],
                       title="Flujo Mensual — 12 Meses")

    st.divider()

    # Waterfall + By category
    col3, col4 = st.columns(2)
    with col3:
        wf = ca.waterfall_monthly(date_prefix)
        if not wf.empty:
            waterfall_chart(wf, x="item", y="amount",
                            title=f"Waterfall — {date_prefix}")

    with col4:
        by_cat = ca.by_category(date_prefix)
        if not by_cat.empty:
            data_table(by_cat, title="Detalle por Categoría",
                       currency_cols=["inflow", "outflow", "net_flow"])

    st.divider()

    # Projection (3 scenarios)
    section_title("Proyección a 90 Días", "sparkles")
    proj = ca.projection(90)
    if not proj.empty:
        line_chart(proj, x="date_id",
                   y=["balance_base", "balance_optimistic", "balance_pessimistic"],
                   title="Proyección de Saldo — 3 Escenarios",
                   y_label="Bs")

        if breakeven:
            st.warning(f"Al ritmo actual, el efectivo podría agotarse en **{breakeven} días**.")
        else:
            st.success("El flujo de caja se mantiene positivo en el horizonte de proyección.")

    # Seasonal pattern
    seasonal = ca.seasonal_pattern()
    if not seasonal.empty:
        bar_chart(seasonal, x="month", y="avg_net",
                  title="Patrón Estacional — Flujo Neto Promedio por Mes")

    st.divider()

    engine = get_engine()
    if engine.is_available:
        def run_analysis():
            data = {
                "kpis": kpis,
                "breakeven_days": breakeven,
                "monthly_summary": monthly.to_dict("records") if not monthly.empty else [],
                "projection_summary": proj.head(10).to_dict("records") if not proj.empty else [],
            }
            return engine.analyze_module("cashflow", data, CASHFLOW_ANALYSIS)
        ai_analysis_box("Análisis de Flujo de Caja", run_analysis)
    else:
        ai_analysis_box("Análisis de Flujo de Caja", None)

except Exception as e:
    st.error(f"Error al cargar datos de flujo de caja: {e}")
    st.info("Verifica que la base de datos esté inicializada y tenga datos.")
