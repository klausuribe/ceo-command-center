---
name: streamlit-dashboard
description: >
  Build Streamlit dashboard pages with KPI cards, Plotly charts, interactive tables,
  and AI analysis boxes. Use this skill whenever creating or editing any Streamlit page,
  dashboard component, chart, KPI card, sidebar, or UI element. Triggers on "dashboard",
  "page", "chart", "KPI", "visualization", "streamlit", "UI", "layout", or any request
  involving the app's visual interface.
---

# Streamlit Dashboard Builder

Build professional CEO dashboard pages following these patterns.

## Page Structure Template

Every dashboard page follows this layout:

```python
import streamlit as st
from components.sidebar import render_sidebar
from components.kpi_cards import render_kpi_row
from components.charts import plotly_line, plotly_bar, plotly_donut
from components.ai_analysis_box import render_ai_analysis
from analytics.MODULE_analytics import MODULEAnalytics
from database.db_manager import get_connection

st.set_page_config(page_title="MODULE - CEO Command Center", layout="wide")

# --- Sidebar Filters ---
filters = render_sidebar()

# --- Data Loading ---
@st.cache_data(ttl=300)
def load_data(period, comparison):
    db = get_connection()
    analytics = MODULEAnalytics(db)
    return analytics.get_summary(period, comparison)

data = load_data(filters['period'], filters['comparison'])

# --- KPI Cards Row ---
st.markdown("## Módulo Title")
render_kpi_row([
    {"label": "Métrica 1", "value": data['metric1'], "delta": data['delta1']},
    {"label": "Métrica 2", "value": data['metric2'], "delta": data['delta2']},
])

# --- Charts (use columns for side-by-side) ---
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plotly_line(data['trend']), use_container_width=True)
with col2:
    st.plotly_chart(plotly_bar(data['ranking']), use_container_width=True)

# --- Detail Table ---
st.dataframe(data['detail_table'], use_container_width=True)

# --- AI Analysis (always at bottom) ---
render_ai_analysis(module="MODULE", data=data, period=filters['period'])
```

## KPI Card Pattern

```python
def render_kpi_row(metrics: list[dict]):
    """Render a row of KPI cards. Each dict: {label, value, delta, prefix, suffix}"""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.metric(
                label=m['label'],
                value=f"{m.get('prefix','')}{m['value']:,.2f}{m.get('suffix','')}",
                delta=f"{m.get('delta', 0):+.1f}%" if m.get('delta') else None,
                delta_color="normal"
            )
```

## Chart Patterns (Plotly)

ALWAYS use these Plotly patterns — never matplotlib:

```python
import plotly.express as px
import plotly.graph_objects as go

# Color palette for consistency
COLORS = {
    'primary': '#1f77b4',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff7f0e',
    'info': '#17becf',
    'palette': px.colors.qualitative.Set2
}

def plotly_line(df, x, y, title, color=None):
    fig = px.line(df, x=x, y=y, color=color, title=title)
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified"
    )
    return fig

def plotly_bar(df, x, y, title, orientation='v', color=None):
    fig = px.bar(df, x=x, y=y, color=color, title=title,
                 orientation=orientation, text_auto='.2s')
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def plotly_donut(df, values, names, title):
    fig = px.pie(df, values=values, names=names, title=title, hole=0.4)
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    return fig
```

## AI Analysis Box Pattern

```python
def render_ai_analysis(module, data, period):
    with st.expander("🤖 Análisis de IA", expanded=True):
        if st.button("Generar Análisis", key=f"ai_{module}"):
            with st.spinner("Analizando datos con IA..."):
                from ai.engine import AIEngine
                engine = AIEngine()
                analysis = engine.generate_module_analysis(module, period)
                st.markdown(analysis)
        # Show cached analysis if exists
        elif cached := get_cached_analysis(module, period):
            st.markdown(cached)
```

## Critical Streamlit Rules

1. **ALWAYS `use_container_width=True`** on charts and dataframes
2. **ALWAYS `layout="wide"`** in page config
3. **Use `@st.cache_data(ttl=300)`** on data-loading functions
4. **Use `@st.cache_resource`** for database connections and AI client
5. **Unique `key=` parameter** on every interactive widget
6. **`st.session_state`** for state that persists across reruns
7. **Never `st.experimental_*`** — use current API names
8. **Spanish labels** on all UI text, English in code
9. **Plotly only** — never matplotlib (Plotly is interactive + better in Streamlit)
10. **`st.columns()`** for side-by-side layouts, **`st.tabs()`** for sub-sections

## Multi-Page App Structure

```
app/
├── Home.py                    # Entry point — must be here
└── pages/
    ├── 1_📊_Ventas.py         # Emoji prefix for nice sidebar icons
    ├── 2_💰_Cuentas_por_Cobrar.py
    ├── 3_💳_Cuentas_por_Pagar.py
    ├── 4_📦_Inventarios.py
    ├── 5_📉_Gastos.py
    ├── 6_📈_Financiero.py
    ├── 7_💵_Flujo_de_Caja.py
    └── 8_🤖_AI_Chat.py
```

## After Building Any Page

Verify with the build-and-verify skill:
```bash
timeout 10 streamlit run app/Home.py --server.headless true 2>&1 | head -30
```
If errors appear, fix and re-run until clean startup.
