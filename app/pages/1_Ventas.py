"""Módulo de Ventas — Sales Dashboard."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Ventas — CEO Command Center", page_icon="💰", layout="wide")

from app.components.auth import require_auth
from app.components.sidebar import render_sidebar

require_auth()
from app.components.kpi_cards import kpi_row, format_currency, format_pct
from app.components.charts import line_chart, bar_chart, pie_chart, scatter_chart, treemap_chart
from app.components.tables import data_table, ranking_table
from app.components.ai_analysis_box import ai_analysis_box
from analytics.kpi_calculator import sales_kpis
from analytics import sales_analytics as sa
from ai.engine import get_engine
from ai.prompts.sales_prompts import SALES_ANALYSIS

filters = render_sidebar()
period = filters["period"]
date_prefix = filters["date_prefix"]

st.title("💰 Ventas")

try:
    kpis = sales_kpis(date_prefix)

    kpi_row([
        {"label": "Revenue", "value": format_currency(kpis["revenue"]),
         "delta": f"{kpis['mom_change_pct']:+.1f}% MoM",
         "help": "Ventas totales facturadas en el período seleccionado"},
        {"label": "Margen Bruto", "value": format_pct(kpis["avg_margin"] * 100),
         "help": "Promedio de (precio - costo) / precio por línea de factura"},
        {"label": "Facturas", "value": f"{int(kpis['n_invoices']):,}"},
        {"label": "Clientes Activos", "value": f"{int(kpis['n_customers'])}",
         "help": "Clientes con al menos una factura en el período"},
    ])

    st.divider()

    # Trend + Category breakdown
    col1, col2 = st.columns(2)
    with col1:
        trend = sa.monthly_trend(12)
        if not trend.empty:
            trend = trend.sort_values("period")
            line_chart(trend, x="period", y="revenue", title="Tendencia Mensual de Ventas", y_label="Revenue (Bs)")

    with col2:
        cats = sa.by_category()
        if not cats.empty:
            pie_chart(cats, values="revenue", names="category", title="Revenue por Categoría")

    st.divider()

    # Treemap + Pareto
    col3, col4 = st.columns(2)
    with col3:
        lines = sa.by_product_line()
        if not lines.empty:
            treemap_chart(lines, path=["category", "product_line"], values="revenue",
                          title="Revenue por Categoría → Línea")

    with col4:
        pareto = sa.pareto_products(date_prefix)
        if not pareto.empty:
            bar_chart(pareto.head(20), x="name", y="revenue",
                      color="pareto_class", title="Top 20 Productos (Pareto)")

    st.divider()

    # Rankings side by side
    col5, col6 = st.columns(2)
    with col5:
        top_prod = sa.top_products(10, period=date_prefix)
        ranking_table(top_prod, "Top 10 Productos", "revenue")

    with col6:
        top_cust = sa.top_customers(10, period=date_prefix)
        ranking_table(top_cust, "Top 10 Clientes", "revenue")

    st.divider()

    # Seller performance
    st.subheader("👥 Desempeño Vendedores")
    sellers = sa.seller_performance(date_prefix)
    if not sellers.empty:
        sellers["cumplimiento"] = (sellers["revenue"] / sellers["target_monthly"].replace(0, 1) * 100).round(1)
        data_table(sellers, currency_cols=["revenue", "gross_profit", "target_monthly"],
                   pct_cols=["cumplimiento"])
    else:
        st.info("No hay datos de vendedores para este período.")

    # Scatter: Revenue vs Margin
    scatter_data = sa.revenue_vs_margin_scatter(date_prefix)
    if not scatter_data.empty:
        scatter_chart(scatter_data, x="revenue", y="avg_margin",
                      color="category", hover_name="name",
                      title="Revenue vs Margen por Producto")

    st.divider()

    # AI Analysis
    engine = get_engine()
    if engine.is_available:
        def run_analysis():
            import json
            data = {
                "kpis": kpis,
                "top_products": sa.top_products(5, period=date_prefix).to_dict("records"),
                "top_customers": sa.top_customers(5, period=date_prefix).to_dict("records"),
                "sellers": sellers.to_dict("records") if not sellers.empty else [],
            }
            return engine.analyze_module("sales", data,
                SALES_ANALYSIS.replace("{period}", date_prefix))
        ai_analysis_box("Análisis de Ventas", run_analysis)
    else:
        ai_analysis_box("Análisis de Ventas", None)

except Exception as e:
    st.error(f"Error al cargar datos de ventas: {e}")
    st.info("Verifica que la base de datos esté inicializada y tenga datos.")
