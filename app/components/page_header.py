"""Page header helper — renders a title with an SVG icon + optional subtitle."""

from __future__ import annotations

import html

import streamlit as st

from app.components.icons import icon


def page_header(title: str, icon_name: str, subtitle: str | None = None) -> None:
    """Render a page hero title: '<icon>  Title' + muted subtitle line."""
    sub = (
        f'<div class="ccc-page-subtitle">{html.escape(subtitle)}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div class="ccc-page-title">{icon(icon_name, size=24)}'
        f'<span>{html.escape(title)}</span></div>{sub}',
        unsafe_allow_html=True,
    )


def section_title(title: str, icon_name: str | None = None) -> None:
    """Render a section sub-heading with optional leading icon."""
    ic = icon(icon_name, size=16) if icon_name else ""
    st.markdown(
        f'<div class="ccc-section-title">{ic}'
        f'<span>{html.escape(title)}</span></div>',
        unsafe_allow_html=True,
    )
