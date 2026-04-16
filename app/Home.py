"""CEO Command Center — Home / Executive Summary."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="CEO Command Center",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-initialize database on first run (needed for Streamlit Cloud)
from config.settings import DB_PATH
if not Path(DB_PATH).exists():
    from scripts.init_db import init_db
    from scripts.generate_demo_data import main as generate_demo
    init_db()
    generate_demo()

from app.components.theme import apply_theme
from app.components.auth import require_auth
from app.components.sidebar import render_sidebar
from app.components.page_header import page_header, section_title
from app.components.kpi_cards import kpi_row, mini_metric, format_currency, format_pct
from app.components.alerts_panel import alerts_panel
from app.components.ai_analysis_box import ai_analysis_box

apply_theme()
require_auth()

from analytics.kpi_calculator import (
    sales_kpis, receivables_kpis, payables_kpis, inventory_kpis,
    expense_kpis, cashflow_kpis, financial_kpis,
)
from ai.engine import get_engine
from ai.alert_generator import generate_alerts

filters = render_sidebar()
period = filters["period"]
date_prefix = filters["date_prefix"]

page_header(
    "Resumen Ejecutivo",
    "home",
    subtitle=f"Panorama consolidado de la operación · Período {period}",
)

try:
    sx = sales_kpis(date_prefix)
    rx = receivables_kpis()
    px = payables_kpis()
    ix = inventory_kpis()
    ex = expense_kpis(date_prefix)
    cx = cashflow_kpis()
    fx = financial_kpis(period)

    # Row 1: Core financials
    kpi_row([
        {"label": "Ventas del Mes", "value": format_currency(sx["revenue"]),
         "delta": f"{sx['mom_change_pct']:+.1f}% vs mes ant.",
         "icon": "sales"},
        {"label": "Margen Bruto", "value": format_pct(fx["gross_margin_pct"]),
         "help": "Utilidad bruta / Ventas",
         "icon": "chart-pie"},
        {"label": "Utilidad Neta", "value": format_currency(fx["net_income"]),
         "delta": format_pct(fx["net_margin_pct"]) + " margen",
         "delta_color": "off",
         "icon": "trend-up"},
        {"label": "Saldo en Caja", "value": format_currency(cx["current_balance"]),
         "delta": f"{format_currency(cx['month_net'])} neto mes",
         "icon": "coins"},
    ])

    # Row 2: Operations
    kpi_row([
        {"label": "CxC Abiertas", "value": format_currency(rx["total_balance"]),
         "delta": f"DSO: {rx['dso']:.0f} días", "delta_color": "inverse",
         "help": "Cuentas por cobrar pendientes. DSO = días promedio de cobro",
         "icon": "receivable"},
        {"label": "CxP Abiertas", "value": format_currency(px["total_balance"]),
         "delta": f"{int(px['critical_count'])} críticas", "delta_color": "inverse",
         "help": "Cuentas por pagar pendientes. Críticas = vencidas prioridad alta",
         "icon": "payable"},
        {"label": "Inventario", "value": format_currency(ix["total_value"]),
         "delta": f"{ix['stockout_risk']} en riesgo stockout", "delta_color": "inverse",
         "help": "Valor total a costo. Stockout = productos A/B con <7 días",
         "icon": "inventory"},
        {"label": "Gastos vs Presupuesto", "value": format_currency(ex["total_expenses"]),
         "delta": f"{ex['variance_pct']:+.1f}%",
         "delta_color": "inverse",
         "help": "Positivo = sobre presupuesto, negativo = bajo presupuesto",
         "icon": "expenses"},
    ])

    st.divider()

    # Morning Briefing + Alerts side by side
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        engine = get_engine()
        ai_analysis_box(
            title="Morning Briefing",
            analysis_fn=engine.morning_briefing if engine.is_available else None,
            expanded=True,
        )

    with col_right:
        alerts = generate_alerts()
        alerts_panel(alerts, title="Alertas")

    st.divider()

    # Quick ratio overview
    section_title("Indicadores Clave", "bolt")
    r1, r2, r3, r4 = st.columns(4, gap="small")
    with r1:
        mini_metric(
            "Razón Corriente", f"{fx['current_ratio']:.2f}",
            help_text="Activo Corriente / Pasivo Corriente. >1 = cubre deuda CP",
        )
    with r2:
        mini_metric(
            "ROE", format_pct(fx["roe"]),
            help_text="Return on Equity — rentabilidad sobre patrimonio",
        )
    with r3:
        mini_metric(
            "Deuda/Patrimonio", f"{fx['debt_to_equity']:.2f}",
            help_text="<1 = conservador, >2 = alto apalancamiento",
        )
    with r4:
        mini_metric(
            "Cobertura Intereses", f"{fx['interest_coverage']:.1f}x",
            help_text="EBIT / Gastos Financieros. >3x cómodo, <1.5x riesgo",
        )

except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.info("Ejecutá `python scripts/init_db.py` y `python scripts/generate_demo_data.py` primero.")
