"""Reusable Plotly chart wrappers."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st


# Consistent color palette
COLORS = px.colors.qualitative.Set2
COLOR_POSITIVE = "#2ecc71"
COLOR_NEGATIVE = "#e74c3c"
COLOR_WARNING = "#f39c12"
COLOR_PRIMARY = "#3498db"
COLOR_SECONDARY = "#9b59b6"


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str | list[str],
    title: str = "",
    y_label: str = "",
) -> None:
    """Render a line chart."""
    if isinstance(y, list):
        fig = go.Figure()
        for col in y:
            fig.add_trace(go.Scatter(x=df[x], y=df[col], mode="lines+markers", name=col))
    else:
        fig = px.line(df, x=x, y=y, title=title, markers=True)

    fig.update_layout(
        title=title, yaxis_title=y_label,
        hovermode="x unified", height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
    horizontal: bool = False,
    text_auto: bool = True,
) -> None:
    """Render a bar chart."""
    if horizontal:
        fig = px.bar(df, x=y, y=x, title=title, color=color,
                     orientation="h", text_auto=text_auto, color_discrete_sequence=COLORS)
    else:
        fig = px.bar(df, x=x, y=y, title=title, color=color,
                     text_auto=text_auto, color_discrete_sequence=COLORS)
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def stacked_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str = "",
) -> None:
    """Render a stacked bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, title=title,
                 barmode="stack", color_discrete_sequence=COLORS)
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def pie_chart(
    df: pd.DataFrame,
    values: str,
    names: str,
    title: str = "",
    hole: float = 0.4,
) -> None:
    """Render a donut/pie chart."""
    fig = px.pie(df, values=values, names=names, title=title,
                 hole=hole, color_discrete_sequence=COLORS)
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
    size: str | None = None,
    hover_name: str | None = None,
) -> None:
    """Render a scatter plot."""
    fig = px.scatter(df, x=x, y=y, title=title, color=color,
                     size=size, hover_name=hover_name,
                     color_discrete_sequence=COLORS)
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def waterfall_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
) -> None:
    """Render a waterfall chart."""
    measures = ["absolute"] + ["relative"] * (len(df) - 2) + ["total"]
    fig = go.Figure(go.Waterfall(
        x=df[x], y=df[y],
        measure=measures,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": COLOR_POSITIVE}},
        decreasing={"marker": {"color": COLOR_NEGATIVE}},
        totals={"marker": {"color": COLOR_PRIMARY}},
    ))
    fig.update_layout(title=title, height=400, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def gauge_chart(
    value: float,
    title: str = "",
    max_val: float = 100,
    thresholds: tuple[float, float] = (70, 90),
) -> None:
    """Render a gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        gauge={
            "axis": {"range": [0, max_val]},
            "bar": {"color": COLOR_PRIMARY},
            "steps": [
                {"range": [0, thresholds[0]], "color": "#eafaf1"},
                {"range": [thresholds[0], thresholds[1]], "color": "#fef9e7"},
                {"range": [thresholds[1], max_val], "color": "#fdedec"},
            ],
        },
    ))
    fig.update_layout(height=300, margin=dict(l=30, r=30, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def treemap_chart(
    df: pd.DataFrame,
    path: list[str],
    values: str,
    title: str = "",
    color: str | None = None,
) -> None:
    """Render a treemap chart."""
    fig = px.treemap(df, path=path, values=values, title=title,
                     color=color, color_discrete_sequence=COLORS)
    fig.update_layout(height=500, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)
