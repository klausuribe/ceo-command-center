"""AI analysis expandable box — indigo accent + SVG icon."""

from __future__ import annotations

import html

import streamlit as st
from loguru import logger

from app.components.icons import icon


def _header(title: str) -> str:
    # Streamlit expanders concatenate the label with a caret; we render the
    # SVG inline inside the label by leveraging unsafe_allow_html on markdown
    # above, but because expanders do not allow HTML labels, we prefix with
    # a Unicode mark and style the title separately with a subheader-like
    # section title above the expander.
    return (
        f'<div class="ccc-section-title" style="color:var(--ccc-accent);">'
        f'{icon("sparkles", size=16)}<span>{html.escape(title)}</span></div>'
    )


def ai_analysis_box(
    title: str = "Análisis IA",
    analysis_fn=None,
    expanded: bool = False,
) -> None:
    """Render an AI analysis section with indigo accent header."""
    st.markdown(_header(title), unsafe_allow_html=True)

    with st.expander("Ver análisis", expanded=expanded):
        if analysis_fn is None:
            st.info("Análisis IA no disponible. Configurá ANTHROPIC_API_KEY en .env")
            return
        try:
            with st.spinner("Generando análisis con IA…"):
                text = analysis_fn()
            st.markdown(text)
        except RuntimeError as e:
            st.warning(f"{e}")
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            st.error(f"Error al generar análisis: {e}")


def ai_text_block(text: str | None, title: str = "Análisis IA") -> None:
    """Render pre-generated AI text in a styled block."""
    st.markdown(_header(title), unsafe_allow_html=True)
    if not text:
        st.info("Análisis IA no disponible.")
        return
    with st.expander("Ver análisis", expanded=True):
        st.markdown(text)
