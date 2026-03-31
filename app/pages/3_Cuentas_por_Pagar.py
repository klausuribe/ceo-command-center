"""Módulo de Cuentas por Pagar — Payables Dashboard."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="CxP — CEO Command Center", page_icon="📤", layout="wide")

from app.components.auth import require_auth
from app.components.sidebar import render_sidebar

require_auth()
from app.components.kpi_cards import kpi_row, format_currency
from app.components.charts import bar_chart, pie_chart
from app.components.tables import data_table
from app.components.ai_analysis_box import ai_analysis_box
from analytics.kpi_calculator import payables_kpis
from analytics import payables_analytics as pa
from ai.engine import get_engine
from ai.prompts.payables_prompts import PAYABLES_ANALYSIS

filters = render_sidebar()

st.title("📤 Cuentas por Pagar")

try:
    kpis = payables_kpis()
    cvp = pa.cash_vs_payables()

    kpi_row([
        {"label": "Total CxP", "value": format_currency(kpis["total_balance"])},
        {"label": "Vencido", "value": format_currency(kpis["overdue"]),
         "delta_color": "inverse"},
        {"label": "Próx. 7 días", "value": format_currency(kpis["due_next_7d"])},
        {"label": "Cash vs CxP 30d",
         "value": "OK" if cvp["coverage_30d"] else f"Gap: {format_currency(cvp['gap_30d'])}",
         "delta_color": "normal" if cvp["coverage_30d"] else "inverse"},
    ])

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        aging = pa.aging_summary()
        if not aging.empty:
            bar_chart(aging, x="aging_bucket", y="amount", title="Aging Report — CxP")

    with col2:
        vendors = pa.by_vendor()
        if not vendors.empty:
            pie_chart(vendors.head(10), values="balance", names="name",
                      title="CxP por Proveedor (Top 10)")

    st.divider()

    # Priority matrix
    st.subheader("🎯 Priorización de Pagos")
    priority = pa.payment_priority_matrix()
    if not priority.empty:
        data_table(priority[["vendor", "invoice_number", "balance", "due_date",
                             "days_overdue", "priority", "urgency_score"]].head(20),
                   currency_cols=["balance"])

    # Upcoming payments
    st.subheader("📅 Pagos Próximos (30 días)")
    upcoming = pa.upcoming_payments(30)
    if not upcoming.empty:
        data_table(upcoming, currency_cols=["balance"])
    else:
        st.info("No hay pagos programados en los próximos 30 días.")

    # DPO by vendor
    dpo = pa.dpo_by_vendor()
    if not dpo.empty:
        bar_chart(dpo.head(10), x="name", y="avg_dpo",
                  title="DPO por Proveedor (Top 10)")

    st.divider()

    engine = get_engine()
    if engine.is_available:
        def run_analysis():
            data = {
                "kpis": kpis,
                "cash_vs_payables": cvp,
                "aging": aging.to_dict("records") if not aging.empty else [],
                "top_vendors": vendors.head(5).to_dict("records") if not vendors.empty else [],
            }
            return engine.analyze_module("payables", data, PAYABLES_ANALYSIS)
        ai_analysis_box("Análisis de Pagos", run_analysis)
    else:
        ai_analysis_box("Análisis de Pagos", None)

except Exception as e:
    st.error(f"Error: {e}")
