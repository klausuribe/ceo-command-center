"""Módulo de Importación de Datos — Excel/CSV file import wizard."""

import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Importar Datos — CEO Command Center",
    page_icon="📥",
    layout="wide",
)

from datetime import datetime

import pandas as pd

from app.components.auth import require_auth
from app.components.sidebar import render_sidebar
from database.db_manager import table_count
from etl.file_importer import (
    TABLE_REGISTRY,
    apply_mapping,
    auto_map_columns,
    compute_derived_fields,
    generate_template,
    get_import_history,
    get_table_options,
    import_data,
    log_import,
    normalize_dates,
    read_file,
    validate_data,
    validate_mapping,
)

require_auth()
render_sidebar()

st.title("📥 Importar Datos")

tab_import, tab_history = st.tabs(["Importar", "Historial de importaciones"])

# ─── Import tab ─────────────────────────────────────────────────────

with tab_import:
    # Step 0: Table selection + file upload
    st.subheader("1. Seleccionar tabla destino")

    table_options = get_table_options()
    table_labels = [opt["label"] for opt in table_options]
    table_names = [opt["table"] for opt in table_options]

    selected_idx = st.selectbox(
        "Tabla destino",
        range(len(table_labels)),
        format_func=lambda i: table_labels[i],
        key="import_table_idx",
    )
    target_table = table_names[selected_idx]
    config = TABLE_REGISTRY[target_table]

    # Info about the table
    current_rows = table_count(target_table)
    col_info, col_template = st.columns([2, 1])
    with col_info:
        st.caption(
            f"Registros actuales: **{current_rows:,}** | "
            f"Columnas requeridas: **{', '.join(config.required_columns)}**"
        )
    with col_template:
        template_df = generate_template(target_table)
        buffer = BytesIO()
        template_df.to_excel(buffer, index=False, engine="openpyxl")
        st.download_button(
            "Descargar plantilla Excel",
            data=buffer.getvalue(),
            file_name=f"plantilla_{target_table}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.divider()

    # Import mode
    mode = st.radio(
        "Modo de importación",
        ["append", "replace"],
        format_func=lambda m: "Agregar registros" if m == "append" else "Reemplazar todo (borrar + cargar)",
        horizontal=True,
        key="import_mode",
    )
    if mode == "replace":
        st.warning(
            f"Esto eliminará **todos** los {current_rows:,} registros existentes "
            f"de {config.display_name} antes de cargar los nuevos."
        )

    st.divider()

    # File upload
    st.subheader("2. Subir archivo")
    uploaded = st.file_uploader(
        "Seleccionar archivo Excel (.xlsx) o CSV (.csv)",
        type=["xlsx", "csv"],
        key="import_file",
    )

    if uploaded is not None:
        # Read file
        try:
            raw_df = read_file(uploaded, uploaded.name)
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            st.stop()

        st.success(f"Archivo leído: **{len(raw_df):,}** filas, **{len(raw_df.columns)}** columnas")

        with st.expander("Vista previa del archivo", expanded=True):
            st.dataframe(raw_df.head(10), use_container_width=True)

        st.divider()

        # Step 1: Column mapping
        st.subheader("3. Mapeo de columnas")
        st.caption("Asigne cada columna del archivo a la columna destino. Las columnas requeridas tienen asterisco (*).")

        initial_mapping = auto_map_columns(list(raw_df.columns), target_table)
        source_options = ["-- No mapear --"] + list(raw_df.columns)

        mapping: dict[str, str | None] = {}

        # Layout: 2 columns of mapping selectors
        cols_left, cols_right = st.columns(2)
        target_cols = list(config.columns.keys())
        mid = (len(target_cols) + 1) // 2

        for i, target_col in enumerate(target_cols):
            col_container = cols_left if i < mid else cols_right
            spec = config.columns[target_col]
            is_required = target_col in config.required_columns
            label = f"{'* ' if is_required else ''}{target_col} ({spec.dtype})"

            # Default selection
            default_source = initial_mapping.get(target_col)
            default_idx = 0
            if default_source and default_source in source_options:
                default_idx = source_options.index(default_source)

            with col_container:
                selected = st.selectbox(
                    label,
                    source_options,
                    index=default_idx,
                    key=f"map_{target_table}_{target_col}",
                )

            mapping[target_col] = None if selected == "-- No mapear --" else selected

        st.divider()

        # Step 2: Validate
        st.subheader("4. Validar y confirmar")

        # Mapping validation
        map_result = validate_mapping(raw_df, mapping, target_table)
        for err in map_result.errors:
            st.error(err)
        for warn in map_result.warnings:
            st.warning(warn)

        if not map_result.is_valid:
            st.info("Corrija los errores de mapeo antes de continuar.")
            st.stop()

        # Apply mapping and validate data
        mapped_df = apply_mapping(raw_df, mapping)
        mapped_df = normalize_dates(mapped_df, target_table)

        data_result = validate_data(mapped_df, target_table)
        for err in data_result.errors:
            st.error(err)
        for warn in data_result.warnings:
            st.warning(warn)

        if not data_result.is_valid:
            st.info("Corrija los errores de datos antes de importar.")
            st.stop()

        # Preview computed fields
        preview_df = compute_derived_fields(mapped_df.head(5).copy(), target_table)
        with st.expander("Vista previa con campos calculados"):
            st.dataframe(preview_df, use_container_width=True)

        # Summary
        st.info(
            f"**{len(mapped_df):,}** registros listos para importar en "
            f"**{config.display_name}** ({target_table}) — modo: "
            f"{'agregar' if mode == 'append' else 'reemplazar'}."
        )

        # Confirm button
        if st.button("Confirmar importación", type="primary", use_container_width=True):
            started = datetime.now()
            try:
                with st.spinner("Importando datos..."):
                    result = import_data(mapped_df, target_table, mode=mode)

                completed = datetime.now()
                log_import(
                    source="excel" if uploaded.name.endswith(".xlsx") else "csv",
                    module=target_table,
                    records=result.rows_inserted,
                    status="success",
                    error_message=None,
                    started_at=started,
                    completed_at=completed,
                )

                st.success(f"{result.message}")
                if result.dim_time_added > 0:
                    st.info(f"Se agregaron {result.dim_time_added} fechas nuevas a la dimensión de tiempo.")

                # Clear caches so dashboard pages show new data
                st.cache_data.clear()

                st.balloons()

            except Exception as e:
                completed = datetime.now()
                log_import(
                    source="excel" if uploaded.name.endswith(".xlsx") else "csv",
                    module=target_table,
                    records=0,
                    status="error",
                    error_message=str(e),
                    started_at=started,
                    completed_at=completed,
                )
                st.error(f"Error durante la importación: {e}")

# ─── History tab ────────────────────────────────────────────────────

with tab_history:
    st.subheader("Historial de importaciones")

    history = get_import_history(limit=100)
    if history.empty:
        st.info("No hay importaciones registradas aún.")
    else:
        # Format for display
        display_df = history.rename(columns={
            "sync_id": "ID",
            "source": "Fuente",
            "module": "Tabla",
            "records_synced": "Registros",
            "status": "Estado",
            "error_message": "Error",
            "started_at": "Inicio",
            "completed_at": "Fin",
            "duration_sec": "Duración (s)",
        })
        st.dataframe(
            display_df[["ID", "Inicio", "Fuente", "Tabla", "Registros", "Estado", "Error", "Duración (s)"]],
            use_container_width=True,
            hide_index=True,
        )
