"""Reusable interactive table components."""

import pandas as pd
import streamlit as st
from config.settings import DEFAULT_CURRENCY


def data_table(
    df: pd.DataFrame,
    title: str | None = None,
    currency_cols: list[str] | None = None,
    pct_cols: list[str] | None = None,
    height: int | None = None,
) -> None:
    """Render an interactive dataframe with formatting."""
    if title:
        st.subheader(title)

    if df.empty:
        st.info("No hay datos disponibles.")
        return

    styled = df.copy()

    # Format currency columns
    if currency_cols:
        for col in currency_cols:
            if col in styled.columns:
                styled[col] = styled[col].apply(lambda x: f"{DEFAULT_CURRENCY} {x:,.2f}" if pd.notna(x) else "-")

    # Format percentage columns
    if pct_cols:
        for col in pct_cols:
            if col in styled.columns:
                styled[col] = styled[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")

    kwargs = {"use_container_width": True, "hide_index": True}
    if height is not None:
        kwargs["height"] = height
    st.dataframe(styled, **kwargs)


def ranking_table(
    df: pd.DataFrame,
    title: str,
    value_col: str,
    name_col: str = "name",
    show_bar: bool = True,
) -> None:
    """Render a ranked table with optional progress bars."""
    if title:
        st.subheader(title)
    if df.empty:
        st.info("No hay datos.")
        return

    display = df[[name_col, value_col]].copy()
    if show_bar and len(display) > 0:
        max_val = display[value_col].max()
        if max_val > 0:
            display["progress"] = display[value_col] / max_val

    st.dataframe(
        display,
        column_config={
            value_col: st.column_config.NumberColumn(format=f"{DEFAULT_CURRENCY} %.0f"),
            "progress": st.column_config.ProgressColumn(
                "Rel.", min_value=0, max_value=1, format="%.0f%%"
            ) if show_bar else None,
        },
        use_container_width=True,
        hide_index=True,
    )
