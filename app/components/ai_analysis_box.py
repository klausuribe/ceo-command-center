"""AI analysis expandable box component."""

import streamlit as st
from loguru import logger


def ai_analysis_box(
    title: str = "Análisis IA",
    analysis_fn: callable = None,
    expanded: bool = False,
) -> None:
    """Render an expandable AI analysis section.

    Args:
        title: Section title
        analysis_fn: Callable that returns the analysis text
        expanded: Whether to start expanded
    """
    with st.expander(f"🤖 {title}", expanded=expanded):
        if analysis_fn is None:
            st.info("Análisis IA no disponible. Configura ANTHROPIC_API_KEY en .env")
            return

        try:
            with st.spinner("Generando análisis con IA..."):
                text = analysis_fn()
            st.markdown(text)
        except RuntimeError as e:
            st.warning(f"⚠️ {e}")
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            st.error(f"Error al generar análisis: {e}")


def ai_text_block(text: str | None, title: str = "Análisis IA") -> None:
    """Render pre-generated AI text in a styled block."""
    if not text:
        st.info("Análisis IA no disponible.")
        return

    with st.expander(f"🤖 {title}", expanded=True):
        st.markdown(text)
