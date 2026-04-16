"""Reusable Plotly chart wrappers — Financial Dashboard (dark) theme."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from app.components.theme import TOKENS, plotly_template


# Semantic palette (used across KPIs, waterfalls, gauges, alerts)
COLORS = TOKENS["series"]
COLOR_POSITIVE = TOKENS["positive"]
COLOR_NEGATIVE = TOKENS["negative"]
COLOR_WARNING = TOKENS["warning"]
COLOR_PRIMARY = TOKENS["info"]
COLOR_SECONDARY = TOKENS["accent"]
COLOR_TEXT_MUTED = TOKENS["text_muted"]


def _apply(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    """Apply the global template + standard chrome to a figure."""
    fig.update_layout(**plotly_template())
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left",
                   font=dict(size=14, color=TOKENS["text"])) if title else None,
        height=height,
        margin=dict(l=10, r=10, t=50 if title else 20, b=20),
    )
    return fig


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
        for i, col in enumerate(y):
            fig.add_trace(go.Scatter(
                x=df[x], y=df[col], mode="lines+markers", name=col,
                line=dict(width=2, color=COLORS[i % len(COLORS)]),
                marker=dict(size=5),
            ))
    else:
        fig = px.line(df, x=x, y=y, markers=True,
                      color_discrete_sequence=[COLORS[0]])
        fig.update_traces(line=dict(width=2), marker=dict(size=5))

    fig.update_layout(hovermode="x unified", yaxis_title=y_label)
    st.plotly_chart(_apply(fig, title), use_container_width=True)


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
        fig = px.bar(df, x=y, y=x, color=color, orientation="h",
                     text_auto=text_auto, color_discrete_sequence=COLORS)
    else:
        fig = px.bar(df, x=x, y=y, color=color,
                     text_auto=text_auto, color_discrete_sequence=COLORS)
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(_apply(fig, title), use_container_width=True)


def stacked_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str = "",
) -> None:
    """Render a stacked bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, barmode="stack",
                 color_discrete_sequence=COLORS)
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(_apply(fig, title), use_container_width=True)


def pie_chart(
    df: pd.DataFrame,
    values: str,
    names: str,
    title: str = "",
    hole: float = 0.55,
) -> None:
    """Render a donut/pie chart."""
    fig = px.pie(df, values=values, names=names, hole=hole,
                 color_discrete_sequence=COLORS)
    fig.update_traces(
        textposition="outside",
        textinfo="label+percent",
        marker=dict(line=dict(color=TOKENS["bg"], width=2)),
    )
    st.plotly_chart(_apply(fig, title), use_container_width=True)


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
    fig = px.scatter(df, x=x, y=y, color=color, size=size,
                     hover_name=hover_name, color_discrete_sequence=COLORS)
    st.plotly_chart(_apply(fig, title), use_container_width=True)


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
        connector={"line": {"color": "rgba(148, 163, 184, 0.25)"}},
        increasing={"marker": {"color": COLOR_POSITIVE}},
        decreasing={"marker": {"color": COLOR_NEGATIVE}},
        totals={"marker": {"color": COLOR_SECONDARY}},
    ))
    st.plotly_chart(_apply(fig, title, height=420), use_container_width=True)


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
        title={"text": title, "font": {"color": TOKENS["text"], "size": 14}},
        number={"font": {"color": TOKENS["text"], "family": "Fira Code"}},
        gauge={
            "axis": {"range": [0, max_val],
                     "tickcolor": TOKENS["text_muted"]},
            "bar": {"color": COLOR_SECONDARY, "thickness": 0.25},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 1,
            "bordercolor": "rgba(148, 163, 184, 0.15)",
            "steps": [
                {"range": [0, thresholds[0]], "color": "rgba(34, 197, 94, 0.18)"},
                {"range": [thresholds[0], thresholds[1]], "color": "rgba(245, 158, 11, 0.22)"},
                {"range": [thresholds[1], max_val], "color": "rgba(239, 68, 68, 0.22)"},
            ],
        },
    ))
    st.plotly_chart(_apply(fig, "", height=280), use_container_width=True)


def treemap_chart(
    df: pd.DataFrame,
    path: list[str],
    values: str,
    title: str = "",
    color: str | None = None,
) -> None:
    """Render a treemap chart."""
    fig = px.treemap(df, path=path, values=values, color=color,
                     color_discrete_sequence=COLORS)
    fig.update_traces(
        marker=dict(line=dict(color=TOKENS["bg"], width=2)),
        textfont=dict(color=TOKENS["text"]),
    )
    st.plotly_chart(_apply(fig, title, height=480), use_container_width=True)


def sparkline(values: list[float], color: str = COLOR_SECONDARY, height: int = 44) -> go.Figure:
    """Tiny sparkline for embedding next to KPI values.

    Returns the figure — caller decides how to render (e.g. via st.plotly_chart
    with a fixed small width, or converting to image). Primary consumer is
    ``kpi_cards.kpi_card`` which uses ``plotly_chart`` in a narrow column.
    """
    fig = go.Figure(go.Scatter(
        y=values, mode="lines",
        line=dict(color=color, width=1.8),
        fill="tozeroy",
        fillcolor=f"rgba(99, 102, 241, 0.15)",
        hoverinfo="skip",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig
