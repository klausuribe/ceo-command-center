"""Módulo de Presupuesto — edición, proyección desde históricos y supuestos.

Granularidad: (año, mes, cuenta) con module='expenses'. El presupuesto
persistido aquí gana sobre fact_expenses.budget_amount en el dashboard de Gastos.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Presupuesto — CEO Command Center",
                   page_icon=":dart:", layout="wide")

from app.components.theme import apply_theme
from app.components.auth import require_auth
from app.components.sidebar import render_sidebar
from app.components.page_header import page_header, section_title
from app.components.kpi_cards import format_currency

apply_theme()
require_auth()

from database.db_manager import query_df, execute_sql
from analytics import budget_projector as bp


MONTH_NAMES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# ── Helpers ───────────────────────────────────────────────────────────────

def _display_grid(grid: pd.DataFrame) -> pd.DataFrame:
    """Convierte la grilla interna (columnas '1'..'12') a DataFrame con
    labels de mes en español para la UI. Mantiene account_id + account_name."""
    if grid.empty:
        return grid
    out = grid[["account_id", "code", "account_name"]].copy()
    for i in range(1, 13):
        out[MONTH_NAMES_ES[i - 1]] = grid[str(i)]
    return out


def _grid_from_display(edited: pd.DataFrame, original: pd.DataFrame) -> list[dict]:
    """Devuelve lista de cambios: (year, month, account_id, target_value) para filas modificadas."""
    changes: list[dict] = []
    # Index por account_id para lookup
    orig_by_id = {int(r["account_id"]): r for r in original.to_dict("records")}
    for row in edited.to_dict("records"):
        aid = int(row["account_id"])
        orig = orig_by_id.get(aid, {})
        for i, month_label in enumerate(MONTH_NAMES_ES, start=1):
            new_val = row.get(month_label)
            old_val = orig.get(month_label)
            # Normalizar NaN
            new_is_nan = new_val is None or (isinstance(new_val, float) and np.isnan(new_val))
            old_is_nan = old_val is None or (isinstance(old_val, float) and np.isnan(old_val))
            if new_is_nan and old_is_nan:
                continue
            if not new_is_nan and not old_is_nan and float(new_val) == float(old_val):
                continue
            changes.append({
                "account_id": aid,
                "month": i,
                "new_value": None if new_is_nan else float(new_val),
                "old_value": None if old_is_nan else float(old_val),
            })
    return changes


def _get_assumptions_df() -> pd.DataFrame:
    return query_df(
        "SELECT assumption_id, description, impact_type, impact_value, impact_pct, "
        "       account_id, category, start_date, end_date, is_active "
        "FROM config_assumptions WHERE module = 'expenses' "
        "ORDER BY is_active DESC, created_at DESC"
    )


def _save_assumption(payload: dict) -> None:
    execute_sql(
        "INSERT INTO config_assumptions "
        "(module, description, impact_type, impact_value, impact_pct, "
        " account_id, category, start_date, end_date, is_active, created_by) "
        "VALUES ('expenses', :desc, :itype, :ival, :ipct, :aid, :cat, :start, :end, 1, 'ui')",
        payload,
    )


def _toggle_assumption(aid: int, active: bool) -> None:
    execute_sql(
        "UPDATE config_assumptions SET is_active = :a WHERE assumption_id = :id",
        {"a": 1 if active else 0, "id": aid},
    )


def _delete_assumption(aid: int) -> None:
    execute_sql(
        "DELETE FROM config_assumptions WHERE assumption_id = :id",
        {"id": aid},
    )


# ── Header + sidebar ──────────────────────────────────────────────────────

filters = render_sidebar()
default_year = date.today().year

page_header(
    "Presupuesto",
    "briefcase",
    subtitle="Edición manual, proyección desde históricos y supuestos ejecutivos",
)

year = st.sidebar.number_input(
    "Año del presupuesto",
    min_value=default_year - 2,
    max_value=default_year + 3,
    value=default_year,
    step=1,
    key="budget_year",
)

st.info(
    "El presupuesto que edites aquí gana sobre el presupuesto automático de "
    "`fact_expenses.budget_amount`. Una celda vacía = usar el fallback original."
)

tab_edit, tab_project, tab_assumptions = st.tabs([
    "📝 Editar presupuesto",
    "📈 Proyectar desde históricos",
    "🧠 Supuestos",
])


# ── TAB 1: Editar ─────────────────────────────────────────────────────────

with tab_edit:
    section_title(f"Grilla de presupuesto · {year}", "edit")

    grid = bp.budgets_grid(int(year))
    if grid.empty:
        st.warning("No hay cuentas de gasto en `dim_accounts`. Verifica la inicialización.")
    else:
        display = _display_grid(grid)

        # data_editor con edición inline
        column_config = {
            "account_id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "code": st.column_config.TextColumn("Código", disabled=True, width="small"),
            "account_name": st.column_config.TextColumn("Cuenta", disabled=True, width="medium"),
        }
        for m in MONTH_NAMES_ES:
            column_config[m] = st.column_config.NumberColumn(
                m, format="%.0f", step=1000.0, min_value=0.0,
            )

        edited = st.data_editor(
            display,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            key=f"budget_editor_{year}",
        )

        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            if st.button("💾 Guardar cambios", type="primary", use_container_width=True):
                changes = _grid_from_display(edited, display)
                saved = 0
                deleted = 0
                for ch in changes:
                    if ch["new_value"] is None:
                        bp.delete_budget(int(year), ch["month"], ch["account_id"])
                        deleted += 1
                    else:
                        bp.save_budget(
                            int(year), ch["month"], ch["account_id"],
                            ch["new_value"], source="manual",
                        )
                        saved += 1
                if saved or deleted:
                    st.success(f"Guardado: {saved} celdas · Eliminado: {deleted}")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.info("No hay cambios para guardar.")
        with col_b:
            if st.button("🗑️ Borrar todo el año", use_container_width=True):
                execute_sql(
                    "DELETE FROM config_budgets WHERE year=:y AND module='expenses'",
                    {"y": int(year)},
                )
                st.cache_data.clear()
                st.success(f"Overrides del año {year} eliminados. Fallback activo.")
                st.rerun()
        with col_c:
            total_overrides = query_df(
                "SELECT COUNT(*) as n, SUM(target_value) as total FROM config_budgets "
                "WHERE year=:y AND module='expenses'", {"y": int(year)},
            )
            n = int(total_overrides["n"].iloc[0]) if not total_overrides.empty else 0
            total = total_overrides["total"].iloc[0] if n else 0
            st.metric(f"Overrides activos {year}",
                      f"{n} celdas",
                      format_currency(float(total) if total else 0))


# ── TAB 2: Proyectar desde históricos ─────────────────────────────────────

with tab_project:
    section_title("Proyección con MA6 + tendencia lineal", "trend-up")

    st.caption(
        "Usa los últimos 6 meses de gastos reales por cuenta + una regresión lineal "
        "para proyectar. Los supuestos activos se aplican como multiplicadores."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        start_month = st.number_input("Mes inicial", 1, 12, value=1, step=1)
    with col2:
        months_ahead = st.number_input("Meses a proyectar", 1, 24, value=12, step=1)
    with col3:
        lookback = st.number_input("Meses de histórico (ventana)", 3, 24, value=6, step=1)

    if st.button("🔮 Generar proyección", type="primary"):
        with st.spinner("Proyectando..."):
            projection = bp.project_all_accounts(
                int(year), int(start_month),
                months_ahead=int(months_ahead),
                lookback=int(lookback),
            )
        st.session_state["budget_projection"] = projection

    projection = st.session_state.get("budget_projection")
    if projection is not None and not projection.empty:
        st.write(f"**{len(projection)} filas proyectadas** — revisa y confirma antes de persistir.")

        # Pivot para vista: cuenta × mes
        pivot = projection.pivot_table(
            index=["account_id", "account_name"],
            columns="month",
            values="target_value",
            aggfunc="first",
        ).reset_index()
        pivot.columns = [
            "account_id", "account_name"
        ] + [MONTH_NAMES_ES[int(c) - 1] for c in pivot.columns[2:]]
        st.dataframe(pivot, use_container_width=True, hide_index=True)

        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("✅ Guardar como presupuesto (source=projected)",
                         type="primary", use_container_width=True):
                count = bp.save_many(projection)
                st.success(f"Persistidas {count} celdas en `config_budgets`.")
                st.session_state.pop("budget_projection", None)
                st.cache_data.clear()
                st.rerun()
        with col_cancel:
            if st.button("❌ Descartar proyección", use_container_width=True):
                st.session_state.pop("budget_projection", None)
                st.rerun()


# ── TAB 3: Supuestos ──────────────────────────────────────────────────────

with tab_assumptions:
    section_title("Supuestos estructurados sobre gastos", "target")

    st.caption(
        "Los supuestos activos se aplican como multiplicadores sobre la proyección. "
        "Ej: aumentar Marketing 15% de abril a junio, o fijar Alquiler en 9000 desde agosto."
    )

    with st.expander("➕ Nuevo supuesto", expanded=False):
        accounts_df = query_df(
            "SELECT account_id, code, name FROM dim_accounts "
            "WHERE account_type = 'expense' ORDER BY code"
        )
        account_options = {"— Todas las cuentas —": None}
        if not accounts_df.empty:
            for row in accounts_df.to_dict("records"):
                label = f"{row['code']} · {row['name']}"
                account_options[label] = int(row["account_id"])

        with st.form("new_assumption", clear_on_submit=True):
            desc = st.text_input("Descripción", placeholder="Ej: Aumento de 15% en marketing Q2")
            col1, col2 = st.columns(2)
            with col1:
                impact_type = st.selectbox(
                    "Tipo de impacto",
                    options=["increase", "decrease", "replace"],
                    format_func=lambda x: {
                        "increase": "Aumento (%)",
                        "decrease": "Descuento (%)",
                        "replace": "Reemplazo (valor absoluto)",
                    }[x],
                )
            with col2:
                account_label = st.selectbox("Cuenta afectada", options=list(account_options.keys()))
                selected_account_id = account_options[account_label]

            col3, col4 = st.columns(2)
            with col3:
                impact_pct = st.number_input(
                    "Porcentaje (si aplica)", min_value=0.0, max_value=500.0,
                    value=0.0, step=1.0,
                    help="Solo relevante para 'increase' y 'decrease'",
                )
            with col4:
                impact_value = st.number_input(
                    "Valor absoluto (si aplica)", min_value=0.0,
                    value=0.0, step=100.0,
                    help="Solo relevante para 'replace'",
                )

            category = st.text_input(
                "Filtro por substring (opcional, case-insensitive)",
                placeholder="Ej: 'marketing' — aplica a toda cuenta que contenga el texto",
            )

            col5, col6 = st.columns(2)
            with col5:
                start = st.date_input("Vigente desde", value=date(int(year), 1, 1))
            with col6:
                end = st.date_input("Vigente hasta", value=date(int(year), 12, 31))

            submitted = st.form_submit_button("Guardar supuesto", type="primary")
            if submitted:
                if not desc.strip():
                    st.error("La descripción es obligatoria.")
                elif impact_type in ("increase", "decrease") and impact_pct == 0.0:
                    st.error("Indica el porcentaje para un aumento/descuento.")
                elif impact_type == "replace" and impact_value == 0.0:
                    st.error("Indica el valor absoluto para un reemplazo.")
                else:
                    _save_assumption({
                        "desc": desc.strip(),
                        "itype": impact_type,
                        "ival": float(impact_value) if impact_value else None,
                        "ipct": float(impact_pct) if impact_pct else None,
                        "aid": selected_account_id,
                        "cat": category.strip() or None,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                    })
                    st.success("Supuesto guardado. Re-proyecta para verlo aplicado.")
                    st.rerun()

    # Lista de supuestos existentes
    assumptions = _get_assumptions_df()
    if assumptions.empty:
        st.info("No hay supuestos registrados. Crea el primero arriba.")
    else:
        st.write(f"**{len(assumptions)} supuestos registrados** ({int(assumptions['is_active'].sum())} activos)")
        for row in assumptions.to_dict("records"):
            aid = int(row["assumption_id"])
            active = bool(row["is_active"])
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
                with c1:
                    st.markdown(f"**{row['description']}**")
                    scope = []
                    if row.get("account_id"):
                        acc = query_df(
                            "SELECT name FROM dim_accounts WHERE account_id=:a",
                            {"a": int(row["account_id"])},
                        )
                        if not acc.empty:
                            scope.append(f"Cuenta: {acc['name'].iloc[0]}")
                    if row.get("category"):
                        scope.append(f"Filtro: '{row['category']}'")
                    if row.get("start_date") or row.get("end_date"):
                        scope.append(f"{row.get('start_date') or '—'} → {row.get('end_date') or '—'}")
                    if scope:
                        st.caption(" · ".join(scope))
                with c2:
                    impact_desc = row["impact_type"] or ""
                    if row["impact_pct"]:
                        impact_desc += f" {row['impact_pct']:+.1f}%"
                    if row["impact_value"]:
                        impact_desc += f" {format_currency(row['impact_value'])}"
                    st.write(impact_desc)
                with c3:
                    new_active = st.toggle(
                        "Activo", value=active, key=f"toggle_{aid}",
                        label_visibility="collapsed",
                    )
                    if new_active != active:
                        _toggle_assumption(aid, new_active)
                        st.rerun()
                with c4:
                    if st.button("🗑️", key=f"del_{aid}", help="Eliminar supuesto"):
                        _delete_assumption(aid)
                        st.rerun()
