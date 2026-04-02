"""Módulo de Inventarios — Inventory Dashboard."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Inventarios — CEO Command Center", page_icon="📦", layout="wide")

from app.components.auth import require_auth
from app.components.sidebar import render_sidebar

require_auth()
from app.components.kpi_cards import kpi_row, format_currency
from app.components.charts import bar_chart, pie_chart, scatter_chart
from app.components.tables import data_table
from app.components.ai_analysis_box import ai_analysis_box
from analytics.kpi_calculator import inventory_kpis
from analytics import inventory_analytics as ia
from ai.engine import get_engine
from ai.prompts.inventory_prompts import INVENTORY_ANALYSIS

filters = render_sidebar()

st.title("📦 Inventarios")

try:
    kpis = inventory_kpis()

    kpi_row([
        {"label": "Valor Total", "value": format_currency(kpis["total_value"])},
        {"label": "SKUs Activos", "value": f"{int(kpis['total_skus'])}"},
        {"label": "Bajo Reorden", "value": f"{int(kpis['below_reorder'])}",
         "delta": "requieren pedido", "delta_color": "inverse"},
        {"label": "Dead Stock", "value": format_currency(kpis["dead_stock_value"]),
         "delta": f"{int(kpis['dead_stock_count'])} SKUs", "delta_color": "inverse"},
    ])

    st.divider()

    # ABC + Value by category
    col1, col2 = st.columns(2)
    with col1:
        import pandas as pd
        abc_dist = pd.DataFrame(kpis["abc_distribution"])
        if not abc_dist.empty:
            pie_chart(abc_dist, values="value", names="rotation_class",
                      title="Valor por Clasificación de Rotación")

    with col2:
        val_cat = ia.inventory_value_by_category()
        if not val_cat.empty:
            bar_chart(val_cat, x="category", y="total_value",
                      title="Valor de Inventario por Categoría")

    st.divider()

    # Rotation scatter: value vs days of stock
    rotation = ia.rotation_analysis()
    if not rotation.empty:
        scatter_chart(rotation, x="total_value", y="days_of_stock",
                      color="rotation_class", hover_name="name",
                      title="Valor vs Días de Stock (Cuadrantes de Rotación)")

    st.divider()

    # Critical levels
    crits = ia.critical_levels()

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("⚠️ Bajo Punto de Reorden")
        data_table(crits["below_reorder"])

    with col4:
        st.subheader("🗑️ Dead Stock")
        data_table(crits["dead_stock"],
                   currency_cols=["total_value"])

    # Overstock
    if not crits["overstock"].empty:
        st.subheader("📦 Sobre-stock (>90 días)")
        data_table(crits["overstock"].head(15),
                   currency_cols=["total_value"])

    st.divider()

    # Reorder suggestions
    st.subheader("🛒 Sugerencias de Reposición")
    reorder = ia.reorder_suggestions()
    if not reorder.empty:
        data_table(reorder)
    else:
        st.success("Todos los productos están sobre el punto de reorden.")

    st.divider()

    engine = get_engine()
    if engine.is_available:
        def run_analysis():
            data = {
                "kpis": kpis,
                "below_reorder": crits["below_reorder"].to_dict("records"),
                "dead_stock": crits["dead_stock"].to_dict("records"),
                "value_by_category": val_cat.to_dict("records") if not val_cat.empty else [],
            }
            return engine.analyze_module("inventory", data, INVENTORY_ANALYSIS)
        ai_analysis_box("Análisis de Inventario", run_analysis)
    else:
        ai_analysis_box("Análisis de Inventario", None)

except Exception as e:
    st.error(f"Error: {e}")
