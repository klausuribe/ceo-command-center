"""Módulo Financiero — Financial Statements Dashboard."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Financiero — CEO Command Center", page_icon="📈", layout="wide")

from app.components.auth import require_auth
from app.components.sidebar import render_sidebar

require_auth()
from app.components.kpi_cards import kpi_row, format_currency, format_pct
from app.components.charts import line_chart, bar_chart
from app.components.tables import data_table
from app.components.ai_analysis_box import ai_analysis_box
from analytics.kpi_calculator import financial_kpis
from analytics import financial_analytics as fa
from ai.engine import get_engine
from ai.prompts.financial_prompts import FINANCIAL_ANALYSIS

filters = render_sidebar()
period = filters["period"]  # Always YYYY-MM for financial queries

st.title("📈 Estados Financieros")

try:
    kpis = financial_kpis(period)

    # Margins row
    kpi_row([
        {"label": "Revenue", "value": format_currency(kpis["revenue"])},
        {"label": "Margen Bruto", "value": format_pct(kpis["gross_margin_pct"])},
        {"label": "Margen Operativo", "value": format_pct(kpis["operating_margin_pct"])},
        {"label": "Margen Neto", "value": format_pct(kpis["net_margin_pct"])},
    ])

    # Ratios row
    kpi_row([
        {"label": "Razón Corriente", "value": f"{kpis['current_ratio']:.2f}",
         "help": "Activo Corriente / Pasivo Corriente"},
        {"label": "Prueba Ácida", "value": f"{kpis['quick_ratio']:.2f}"},
        {"label": "ROE", "value": format_pct(kpis["roe"])},
        {"label": "ROA", "value": format_pct(kpis["roa"])},
    ])

    st.divider()

    # Income Statement + Balance Sheet tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Estado de Resultados", "Balance General",
                                        "Ratios & Tendencias", "Eficiencia"])

    with tab1:
        is_df = fa.income_statement(period)
        if not is_df.empty:
            cs = fa.common_size_analysis(period)
            data_table(cs, title="Estado de Resultados",
                       currency_cols=["amount", "prev_period", "prev_year", "budget"],
                       pct_cols=["pct_of_revenue"])

    with tab2:
        bs_df = fa.balance_sheet(period)
        if not bs_df.empty:
            data_table(bs_df, title="Balance General",
                       currency_cols=["amount", "prev_period", "prev_year"])

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            margins = fa.margin_trend(12)
            if not margins.empty:
                margins = margins.sort_values("period")
                line_chart(margins, x="period",
                           y=["gross_margin_pct", "operating_margin_pct", "net_margin_pct"],
                           title="Tendencia de Márgenes (%)")

        with col2:
            liquidity = fa.liquidity_trend(12)
            if not liquidity.empty:
                liquidity = liquidity.sort_values("period")
                line_chart(liquidity, x="period",
                           y=["current_ratio", "quick_ratio"],
                           title="Tendencia de Liquidez")

        leverage = fa.leverage_trend(12)
        if not leverage.empty:
            leverage = leverage.sort_values("period")
            line_chart(leverage, x="period",
                       y=["debt_to_equity", "debt_to_assets"],
                       title="Tendencia de Apalancamiento")

    with tab4:
        eff = fa.efficiency_ratios(period)
        kpi_row([
            {"label": "DSO", "value": f"{eff['dso']:.0f} días",
             "help": "Days Sales Outstanding"},
            {"label": "DPO", "value": f"{eff['dpo']:.0f} días",
             "help": "Days Payable Outstanding"},
            {"label": "DIO", "value": f"{eff['dio']:.0f} días",
             "help": "Days Inventory Outstanding"},
            {"label": "CCC", "value": f"{eff['ccc']:.0f} días",
             "delta": eff["interpretation"],
             "help": "Cash Conversion Cycle = DSO + DIO - DPO"},
        ])

    st.divider()

    engine = get_engine()
    if engine.is_available:
        def run_analysis():
            data = {
                "kpis": kpis,
                "efficiency": fa.efficiency_ratios(period),
                "income_statement_summary": is_df.to_dict("records") if not is_df.empty else [],
            }
            return engine.analyze_module("financial", data,
                FINANCIAL_ANALYSIS.replace("{period}", period))
        ai_analysis_box("Análisis Financiero", run_analysis)
    else:
        ai_analysis_box("Análisis Financiero", None)

except Exception as e:
    st.error(f"Error: {e}")
