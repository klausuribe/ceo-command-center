"""Módulo de Chat IA + What-If — AI-Powered Business Chat & Scenario Simulator."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Chat IA — CEO Command Center", page_icon="🤖", layout="wide")

from app.components.auth import require_auth
from app.components.sidebar import render_sidebar

require_auth()
from app.components.whatif_panel import whatif_sliders, display_results
from app.components.ai_analysis_box import ai_analysis_box
from ai.engine import get_engine
from ai.chat_engine import ChatEngine
from ai.whatif_simulator import simulate_scenario, ai_scenario_analysis
from database.db_manager import query_df, execute_sql

filters = render_sidebar()
period = filters["period"]
date_prefix = filters["date_prefix"]

st.title("🤖 Chat IA & Simulador")

engine = get_engine()

if not engine.is_available:
    st.warning("⚠️ API de Claude no configurada. Agrega ANTHROPIC_API_KEY en .env")
    st.stop()

# Initialize session state
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = ChatEngine(engine)
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Three tabs: Chat, What-If, Supuestos ─────────────────────────────
tab_chat, tab_whatif, tab_assumptions = st.tabs(["💬 Chat", "🔮 What-If", "📋 Supuestos"])

# ═══════════════════════════════════════════════════════════════════
#  TAB 1: CHAT
# ═══════════════════════════════════════════════════════════════════
with tab_chat:
    st.caption("Pregunta sobre tu negocio — respuestas con datos reales")

    # Suggested questions (only when empty)
    if not st.session_state.messages:
        st.markdown("**Preguntas sugeridas:**")
        suggestions = [
            "¿Cuál es el estado general de mi negocio hoy?",
            "¿Cuáles son mis 5 clientes que más me deben?",
            "¿Qué productos debería descontinuar?",
            "Compara mis ventas de este mes vs el mes pasado",
            "Asume que las ventas bajan 15% el próximo mes",
            "¿Qué pasa si un cliente grande retrasa su pago 30 días?",
        ]
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(s, key=f"sug_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": s})
                    st.rerun()

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # New message input
    if prompt := st.chat_input("Pregunta sobre tu negocio..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analizando datos..."):
                response = st.session_state.chat_engine.process_message(
                    prompt,
                    chat_history=st.session_state.messages[:-1],
                    active_module=None,
                )
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    # Handle suggestion button clicks (pending user message without response)
    if (st.session_state.messages
        and st.session_state.messages[-1]["role"] == "user"
        and len(st.session_state.messages) >= 1):

        has_response = any(
            i > 0 and st.session_state.messages[i-1]["role"] == "user"
            and msg["role"] == "assistant"
            for i, msg in enumerate(st.session_state.messages)
            if i == len(st.session_state.messages) - 1
        )

        if not has_response and len(st.session_state.messages) % 2 == 1:
            last_msg = st.session_state.messages[-1]["content"]
            with st.chat_message("assistant"):
                with st.spinner("Analizando datos..."):
                    response = st.session_state.chat_engine.process_message(
                        last_msg,
                        chat_history=st.session_state.messages[:-1],
                        active_module=None,
                    )
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Limpiar conversación", key="clear_chat"):
            st.session_state.messages = []
            st.session_state.chat_engine = ChatEngine(engine)
            st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  TAB 2: WHAT-IF SIMULATOR
# ═══════════════════════════════════════════════════════════════════
with tab_whatif:
    st.caption("Simula escenarios y analiza el impacto en tu negocio")

    scenario = whatif_sliders()

    # Only simulate if something changed from defaults
    has_changes = any(v != 0 for v in scenario.values())

    if has_changes:
        results = simulate_scenario(scenario, date_prefix)
        display_results(results)

        st.divider()

        # AI interpretation
        if engine.is_available:
            def run_whatif_ai():
                return ai_scenario_analysis(engine, scenario, results)
            ai_analysis_box("Análisis IA del Escenario", run_whatif_ai)

        # Save as assumption
        st.divider()
        st.subheader("💾 Guardar como Supuesto")
        desc = st.text_input(
            "Descripción del supuesto",
            value=_scenario_description(scenario),
            key="assumption_desc",
        )
        if st.button("Guardar Supuesto", key="save_assumption", type="primary"):
            try:
                execute_sql(
                    "INSERT INTO config_assumptions "
                    "(module, description, impact_type, impact_pct, is_active, created_by) "
                    "VALUES (:mod, :desc, :type, :pct, 1, 'whatif')",
                    {
                        "mod": "general",
                        "desc": desc,
                        "type": "increase" if scenario.get("sales_change_pct", 0) >= 0 else "decrease",
                        "pct": scenario.get("sales_change_pct", 0),
                    },
                )
                st.success("Supuesto guardado correctamente.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")
    else:
        st.info("Ajusta los sliders para simular un escenario.")


# ═══════════════════════════════════════════════════════════════════
#  TAB 3: SUPUESTOS ACTIVOS
# ═══════════════════════════════════════════════════════════════════
with tab_assumptions:
    st.caption("Supuestos que afectan las proyecciones del sistema")

    assumptions = query_df(
        "SELECT assumption_id, created_at, module, description, "
        "impact_type, impact_pct, is_active, created_by "
        "FROM config_assumptions ORDER BY created_at DESC"
    )

    if assumptions.empty:
        st.info("No hay supuestos guardados. Usa el chat o el simulador What-If para crear supuestos.")
    else:
        # Active assumptions
        active = assumptions[assumptions["is_active"] == 1]
        inactive = assumptions[assumptions["is_active"] != 1]

        if not active.empty:
            st.subheader(f"✅ Activos ({len(active)})")
            for _, row in active.iterrows():
                col1, col2 = st.columns([5, 1])
                with col1:
                    icon = "📈" if row["impact_type"] == "increase" else "📉" if row["impact_type"] == "decrease" else "📋"
                    st.markdown(f"{icon} **{row['description']}**")
                    st.caption(f"Módulo: {row['module']} | Creado: {row['created_at']} | Por: {row['created_by']}")
                with col2:
                    if st.button("Desactivar", key=f"deact_{row['assumption_id']}"):
                        execute_sql(
                            "UPDATE config_assumptions SET is_active = 0 WHERE assumption_id = :id",
                            {"id": int(row["assumption_id"])},
                        )
                        st.rerun()

        if not inactive.empty:
            with st.expander(f"Inactivos ({len(inactive)})"):
                for _, row in inactive.iterrows():
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"~~{row['description']}~~")
                        st.caption(f"Módulo: {row['module']} | Creado: {row['created_at']}")
                    with col2:
                        if st.button("Reactivar", key=f"react_{row['assumption_id']}"):
                            execute_sql(
                                "UPDATE config_assumptions SET is_active = 1 WHERE assumption_id = :id",
                                {"id": int(row["assumption_id"])},
                            )
                            st.rerun()

    # Manual assumption input
    st.divider()
    st.subheader("➕ Nuevo Supuesto Manual")
    with st.form("new_assumption"):
        module = st.selectbox("Módulo", ["general", "sales", "receivables", "payables",
                                          "inventory", "expenses", "cashflow"])
        description = st.text_area("Descripción", placeholder="Ej: Las ventas bajan 15% en abril por temporada baja")
        impact_type = st.selectbox("Tipo de Impacto", ["increase", "decrease", "replace"])
        impact_pct = st.number_input("Impacto (%)", min_value=-100.0, max_value=100.0, value=0.0, step=5.0)

        if st.form_submit_button("Guardar", type="primary"):
            if description:
                execute_sql(
                    "INSERT INTO config_assumptions "
                    "(module, description, impact_type, impact_pct, is_active, created_by) "
                    "VALUES (:mod, :desc, :type, :pct, 1, 'manual')",
                    {"mod": module, "desc": description, "type": impact_type, "pct": impact_pct},
                )
                st.success("Supuesto guardado.")
                st.rerun()
            else:
                st.warning("Escribe una descripción.")


def _scenario_description(scenario: dict) -> str:
    """Generate a human-readable description of a scenario."""
    parts = []
    if scenario.get("sales_change_pct"):
        parts.append(f"Ventas {int(scenario['sales_change_pct']):+d}%")
    if scenario.get("cost_change_pct"):
        parts.append(f"Costos {int(scenario['cost_change_pct']):+d}%")
    if scenario.get("opex_change_pct"):
        parts.append(f"Gastos Op. {int(scenario['opex_change_pct']):+d}%")
    if scenario.get("dso_change_days"):
        parts.append(f"DSO {int(scenario['dso_change_days']):+d} días")
    if scenario.get("new_investment"):
        parts.append(f"Inversión Bs {int(scenario['new_investment']):,}")
    if scenario.get("fixed_expense_change"):
        parts.append(f"Gastos fijos {int(scenario['fixed_expense_change']):+,}/mes")
    return " | ".join(parts) if parts else "Sin cambios"
