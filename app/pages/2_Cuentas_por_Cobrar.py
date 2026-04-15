"""Módulo de Cuentas por Cobrar — Receivables Dashboard."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="CxC — CEO Command Center", page_icon="📥", layout="wide")

from app.components.auth import require_auth
from app.components.sidebar import render_sidebar

require_auth()
from app.components.kpi_cards import kpi_row, format_currency, format_pct
from app.components.charts import bar_chart, stacked_bar, pie_chart
from app.components.tables import data_table, ranking_table
from app.components.ai_analysis_box import ai_analysis_box
from analytics.kpi_calculator import receivables_kpis
from analytics import receivables_analytics as ra
from ai.engine import get_engine
from ai.prompts.receivables_prompts import RECEIVABLES_ANALYSIS

filters = render_sidebar()

st.title("📥 Cuentas por Cobrar")

try:
    kpis = receivables_kpis()

    kpi_row([
        {"label": "Saldo Total CxC", "value": format_currency(kpis["total_balance"]),
         "help": "Suma de facturas pendientes de cobro (excluye pagadas)"},
        {"label": "Vencido", "value": format_currency(kpis["overdue"]),
         "delta_color": "inverse",
         "help": "Facturas que superaron su fecha de vencimiento"},
        {"label": "DSO", "value": f"{kpis['dso']:.0f} días",
         "help": "Days Sales Outstanding — días promedio para cobrar. Ideal: <45 días"},
        {"label": "Concentración Top 5", "value": format_pct(kpis["top5_concentration_pct"]),
         "help": "% del saldo CxC concentrado en los 5 mayores deudores. >50% = riesgo alto"},
    ])

    st.divider()

    # Aging chart + Pie
    col1, col2 = st.columns(2)
    with col1:
        aging = ra.aging_summary()
        if not aging.empty:
            bar_chart(aging, x="aging_bucket", y="amount", title="Aging Report — CxC")

    with col2:
        if not aging.empty:
            pie_chart(aging, values="amount", names="aging_bucket", title="Distribución de Aging")

    st.divider()

    # Top debtors + DSO by customer
    col3, col4 = st.columns(2)
    with col3:
        debtors = ra.top_debtors(10)
        ranking_table(debtors, "Top 10 Deudores", "balance")

    with col4:
        dso = ra.dso_by_customer()
        if not dso.empty:
            bar_chart(dso.head(10), x="name", y="avg_days_overdue",
                      title="DSO por Cliente (Top 10 más lentos)")

    st.divider()

    # Credit scoring
    st.subheader("📊 Credit Score")
    scores = ra.credit_score()
    if not scores.empty:
        data_table(scores[["name", "segment", "score", "risk_level", "on_time_pct",
                           "total_balance"]].head(20),
                   currency_cols=["total_balance"], pct_cols=["on_time_pct"])
    else:
        st.info("No hay suficientes datos para calcular credit scores.")

    # Upcoming due
    st.subheader("📅 Próximos Vencimientos (7 días)")
    upcoming = ra.upcoming_due(7)
    if not upcoming.empty:
        data_table(upcoming, currency_cols=["balance", "original_amount"])
    else:
        st.info("No hay facturas por vencer en los próximos 7 días.")

    # Collection trend
    coll = ra.collection_rate_trend(12)
    if not coll.empty:
        coll = coll.sort_values("period")
        from app.components.charts import line_chart
        line_chart(coll, x="period", y="rate_pct", title="Tasa de Cobro Mensual (%)")

    st.divider()

    # AI Analysis
    engine = get_engine()
    if engine.is_available:
        def run_analysis():
            import json
            data = {
                "kpis": kpis,
                "aging": aging.to_dict("records") if not aging.empty else [],
                "top_debtors": debtors.to_dict("records") if not debtors.empty else [],
            }
            return engine.analyze_module("receivables", data, RECEIVABLES_ANALYSIS)
        ai_analysis_box("Análisis de Cobranza", run_analysis)
    else:
        ai_analysis_box("Análisis de Cobranza", None)

except Exception as e:
    st.error(f"Error al cargar datos de cobranza: {e}")
    st.info("Verifica que la base de datos esté inicializada y tenga datos.")
