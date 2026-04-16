"""Módulo de Gastos — Expenses Dashboard."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Gastos — CEO Command Center", page_icon=":money_with_wings:", layout="wide")

from app.components.theme import apply_theme
from app.components.auth import require_auth
from app.components.sidebar import render_sidebar
from app.components.page_header import page_header, section_title

apply_theme()
require_auth()
from app.components.kpi_cards import kpi_row, format_currency, format_pct
from app.components.charts import line_chart, bar_chart, pie_chart, gauge_chart
from app.components.tables import data_table
from app.components.ai_analysis_box import ai_analysis_box
from analytics.kpi_calculator import expense_kpis
from analytics import expense_analytics as ea
from ai.engine import get_engine
from ai.prompts.expenses_prompts import EXPENSE_ANALYSIS

filters = render_sidebar()
period = filters["period"]
date_prefix = filters["date_prefix"]

page_header("Gastos", "expenses",
            subtitle=f"Real vs presupuesto, centros de costo y variaciones · {date_prefix}")

try:
    kpis = expense_kpis(date_prefix)

    kpi_row([
        {"label": "Gastos del Mes", "value": format_currency(kpis["total_expenses"]),
         "icon": "expenses"},
        {"label": "Presupuesto", "value": format_currency(kpis["total_budget"]),
         "icon": "briefcase"},
        {"label": "Variación", "value": format_currency(kpis["total_variance"]),
         "delta": f"{kpis['variance_pct']:+.1f}%",
         "delta_color": "inverse",
         "help": "Diferencia entre gasto real y presupuestado. Positivo = sobre presupuesto",
         "icon": "trend-up"},
        {"label": "Ejecución", "value": format_pct(
            kpis["total_expenses"] / kpis["total_budget"] * 100 if kpis["total_budget"] else 0),
         "help": "% del presupuesto mensual consumido. Ideal: 90-100%",
         "icon": "chart-pie"},
    ])

    st.divider()

    # Trend + Gauge
    col1, col2 = st.columns([2, 1])
    with col1:
        trend = ea.monthly_trend(12)
        if not trend.empty:
            trend = trend.sort_values("period")
            line_chart(trend, x="period", y=["actual", "budget"],
                       title="Gastos vs Presupuesto — Tendencia 12 Meses")

    with col2:
        exec_pct = kpis["total_expenses"] / kpis["total_budget"] * 100 if kpis["total_budget"] else 0
        gauge_chart(exec_pct, title="Ejecución Presupuestal", max_val=130,
                    thresholds=(90, 110))

    st.divider()

    # By cost center + Fixed vs variable
    col3, col4 = st.columns(2)
    with col3:
        cc = ea.by_cost_center(date_prefix)
        if not cc.empty:
            section_title("Centro de Costo — Semáforo", "filter")
            data_table(cc, currency_cols=["actual", "budget", "variance"],
                       pct_cols=["variance_pct"])

    with col4:
        fv = ea.fixed_vs_variable(date_prefix)
        if not fv.empty:
            pie_chart(fv, values="actual", names="category",
                      title="Fijos vs Variables vs Semi-variables")

    st.divider()

    # By account detail
    section_title("Detalle por Cuenta", "briefcase")
    by_acc = ea.by_account(date_prefix)
    if not by_acc.empty:
        data_table(by_acc, currency_cols=["actual", "budget", "variance"],
                   pct_cols=["variance_pct"])

    # Anomalies
    anomalies = ea.anomalies(date_prefix)
    if not anomalies.empty:
        section_title("Gastos Inusuales", "alert")
        data_table(anomalies[["account", "amount", "hist_mean", "z_score"]],
                   currency_cols=["amount", "hist_mean"])

    # YTD consumption
    section_title("Consumo Presupuestal YTD", "chart-pie")
    ytd = ea.ytd_budget_consumption()
    if not ytd.empty:
        bar_chart(ytd, x="account", y="consumption_pct",
                  title="% Consumo YTD por Cuenta")

    st.divider()

    engine = get_engine()
    if engine.is_available:
        def run_analysis():
            data = {
                "kpis": kpis,
                "by_cost_center": cc.to_dict("records") if not cc.empty else [],
                "anomalies": anomalies.to_dict("records") if not anomalies.empty else [],
            }
            return engine.analyze_module("expenses", data,
                EXPENSE_ANALYSIS.replace("{period}", date_prefix))
        ai_analysis_box("Análisis de Gastos", run_analysis)
    else:
        ai_analysis_box("Análisis de Gastos", None)

except Exception as e:
    st.error(f"Error al cargar datos de gastos: {e}")
    st.info("Verifica que la base de datos esté inicializada y tenga datos.")
