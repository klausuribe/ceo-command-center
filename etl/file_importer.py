"""Excel/CSV file importer for the CEO Command Center data warehouse.

Reads uploaded files, maps columns to target tables, validates data,
computes derived fields, and inserts via db_manager.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime
from io import BytesIO
from typing import Any, BinaryIO

import pandas as pd
from loguru import logger

from database.db_manager import execute_sql, insert_df, query_df


# ─── Column specification ───────────────────────────────────────────

@dataclass
class ColSpec:
    dtype: str          # "int", "float", "str", "date", "bool"
    required: bool
    sample: Any         # sample value for template download


@dataclass
class TableConfig:
    display_name: str                       # Spanish label for UI
    group: str                              # "Dimensiones" | "Transacciones"
    columns: dict[str, ColSpec]
    required_columns: list[str]             # minimum for a valid import
    computed_columns: list[str] | None = None  # auto-derived if missing
    fk_checks: dict[str, str] | None = None   # col -> dim table
    date_columns: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]       # blocking
    warnings: list[str]     # informational


@dataclass
class ImportResult:
    rows_inserted: int
    dim_time_added: int
    message: str


# ─── Table registry ─────────────────────────────────────────────────

TABLE_REGISTRY: dict[str, TableConfig] = {
    # ── Dimensions ──
    "dim_products": TableConfig(
        display_name="Productos",
        group="Dimensiones",
        columns={
            "sku": ColSpec("str", False, "ELE-SMA-0001"),
            "name": ColSpec("str", True, "Smartphone Galaxy"),
            "category": ColSpec("str", False, "Electrónica"),
            "product_line": ColSpec("str", False, "Smartphones"),
            "brand": ColSpec("str", False, "Samsung"),
            "unit_cost": ColSpec("float", False, 1500.0),
            "list_price": ColSpec("float", False, 2200.0),
            "margin_pct": ColSpec("float", False, 0.32),
            "is_active": ColSpec("bool", False, 1),
        },
        required_columns=["name"],
    ),
    "dim_customers": TableConfig(
        display_name="Clientes",
        group="Dimensiones",
        columns={
            "name": ColSpec("str", True, "Importadora Oriente SRL"),
            "customer_code": ColSpec("str", False, "CLI-0001"),
            "segment": ColSpec("str", False, "A"),
            "city": ColSpec("str", False, "Santa Cruz"),
            "region": ColSpec("str", False, "Oriente"),
            "credit_limit": ColSpec("float", False, 50000.0),
            "payment_terms": ColSpec("str", False, "30 días"),
            "assigned_seller": ColSpec("str", False, "Carlos Mendoza"),
            "is_active": ColSpec("bool", False, 1),
            "created_date": ColSpec("date", False, "2025-01-15"),
        },
        required_columns=["name"],
    ),
    "dim_vendors": TableConfig(
        display_name="Proveedores",
        group="Dimensiones",
        columns={
            "name": ColSpec("str", True, "Distribuidora Nacional SRL"),
            "vendor_code": ColSpec("str", False, "PROV-0001"),
            "category": ColSpec("str", False, "Nacional"),
            "country": ColSpec("str", False, "Bolivia"),
            "currency": ColSpec("str", False, "BOB"),
            "payment_terms": ColSpec("str", False, "30 días"),
            "lead_time_days": ColSpec("int", False, 7),
            "is_active": ColSpec("bool", False, 1),
        },
        required_columns=["name"],
    ),
    "dim_sellers": TableConfig(
        display_name="Vendedores",
        group="Dimensiones",
        columns={
            "name": ColSpec("str", True, "Carlos Mendoza"),
            "team": ColSpec("str", False, "Ventas Directas"),
            "region": ColSpec("str", False, "Oriente"),
            "target_monthly": ColSpec("float", False, 120000.0),
            "is_active": ColSpec("bool", False, 1),
        },
        required_columns=["name"],
    ),
    "dim_accounts": TableConfig(
        display_name="Plan de Cuentas",
        group="Dimensiones",
        columns={
            "code": ColSpec("str", True, "4100"),
            "name": ColSpec("str", True, "Ingresos por Ventas"),
            "account_type": ColSpec("str", False, "income"),
            "parent_group": ColSpec("str", False, "Ingresos Operacionales"),
            "sub_group": ColSpec("str", False, "Ventas"),
            "is_active": ColSpec("bool", False, 1),
        },
        required_columns=["code", "name"],
    ),
    "dim_cost_centers": TableConfig(
        display_name="Centros de Costo",
        group="Dimensiones",
        columns={
            "code": ColSpec("str", False, "CC-ADM"),
            "name": ColSpec("str", True, "Administración"),
            "department": ColSpec("str", False, "Administración"),
            "responsible": ColSpec("str", False, "Gerente General"),
            "budget_annual": ColSpec("float", False, 500000.0),
        },
        required_columns=["name"],
    ),

    # ── Facts ──
    "fact_sales": TableConfig(
        display_name="Ventas",
        group="Transacciones",
        columns={
            "date_id": ColSpec("date", True, "2026-03-15"),
            "invoice_number": ColSpec("str", False, "FAC-001005"),
            "product_id": ColSpec("int", True, 1),
            "customer_id": ColSpec("int", True, 1),
            "seller_id": ColSpec("int", False, 1),
            "quantity": ColSpec("float", True, 5.0),
            "unit_price": ColSpec("float", True, 2200.0),
            "unit_cost": ColSpec("float", False, 1500.0),
            "discount_pct": ColSpec("float", False, 0.0),
            "subtotal": ColSpec("float", False, 11000.0),
            "cost_total": ColSpec("float", False, 7500.0),
            "gross_profit": ColSpec("float", False, 3500.0),
            "margin_pct": ColSpec("float", False, 0.318),
            "tax_amount": ColSpec("float", False, 1430.0),
            "total": ColSpec("float", False, 12430.0),
            "currency": ColSpec("str", False, "BOB"),
            "status": ColSpec("str", False, "posted"),
        },
        required_columns=["date_id", "product_id", "customer_id", "quantity", "unit_price"],
        computed_columns=["subtotal", "cost_total", "gross_profit", "margin_pct", "tax_amount", "total"],
        fk_checks={"product_id": "dim_products", "customer_id": "dim_customers", "seller_id": "dim_sellers"},
        date_columns=["date_id"],
    ),
    "fact_receivables": TableConfig(
        display_name="Cuentas por Cobrar",
        group="Transacciones",
        columns={
            "date_id": ColSpec("date", True, "2026-03-15"),
            "invoice_number": ColSpec("str", False, "FAC-001005"),
            "customer_id": ColSpec("int", True, 1),
            "seller_id": ColSpec("int", False, 1),
            "invoice_date": ColSpec("date", True, "2026-03-01"),
            "due_date": ColSpec("date", True, "2026-03-31"),
            "original_amount": ColSpec("float", True, 12430.0),
            "paid_amount": ColSpec("float", False, 0.0),
            "balance": ColSpec("float", False, 12430.0),
            "days_overdue": ColSpec("int", False, 0),
            "aging_bucket": ColSpec("str", False, "current"),
            "status": ColSpec("str", False, "current"),
            "last_payment_date": ColSpec("date", False, ""),
            "collection_notes": ColSpec("str", False, ""),
        },
        required_columns=["date_id", "customer_id", "invoice_date", "due_date", "original_amount"],
        computed_columns=["balance", "days_overdue", "aging_bucket", "status"],
        fk_checks={"customer_id": "dim_customers", "seller_id": "dim_sellers"},
        date_columns=["date_id", "invoice_date", "due_date", "last_payment_date"],
    ),
    "fact_payables": TableConfig(
        display_name="Cuentas por Pagar",
        group="Transacciones",
        columns={
            "date_id": ColSpec("date", True, "2026-03-15"),
            "invoice_number": ColSpec("str", False, "PROV-FAC-0001"),
            "vendor_id": ColSpec("int", True, 1),
            "invoice_date": ColSpec("date", True, "2026-03-01"),
            "due_date": ColSpec("date", True, "2026-03-31"),
            "original_amount": ColSpec("float", True, 8500.0),
            "paid_amount": ColSpec("float", False, 0.0),
            "balance": ColSpec("float", False, 8500.0),
            "days_overdue": ColSpec("int", False, 0),
            "aging_bucket": ColSpec("str", False, "current"),
            "status": ColSpec("str", False, "current"),
            "currency": ColSpec("str", False, "BOB"),
            "priority": ColSpec("str", False, "normal"),
        },
        required_columns=["date_id", "vendor_id", "invoice_date", "due_date", "original_amount"],
        computed_columns=["balance", "days_overdue", "aging_bucket", "status", "priority"],
        fk_checks={"vendor_id": "dim_vendors"},
        date_columns=["date_id", "invoice_date", "due_date"],
    ),
    "fact_inventory": TableConfig(
        display_name="Inventario",
        group="Transacciones",
        columns={
            "snapshot_date": ColSpec("date", True, "2026-03-15"),
            "product_id": ColSpec("int", True, 1),
            "warehouse": ColSpec("str", False, "main"),
            "qty_on_hand": ColSpec("float", True, 150.0),
            "qty_reserved": ColSpec("float", False, 10.0),
            "qty_available": ColSpec("float", False, 140.0),
            "qty_incoming": ColSpec("float", False, 50.0),
            "unit_cost": ColSpec("float", False, 1500.0),
            "total_value": ColSpec("float", False, 225000.0),
            "avg_daily_sales": ColSpec("float", False, 3.5),
            "days_of_stock": ColSpec("float", False, 40.0),
            "reorder_point": ColSpec("float", False, 35.0),
            "reorder_qty": ColSpec("float", False, 100.0),
            "rotation_class": ColSpec("str", False, "A"),
            "last_sale_date": ColSpec("date", False, "2026-03-14"),
            "days_since_last_sale": ColSpec("int", False, 1),
        },
        required_columns=["snapshot_date", "product_id", "qty_on_hand"],
        computed_columns=["qty_available", "total_value"],
        fk_checks={"product_id": "dim_products"},
        date_columns=["snapshot_date", "last_sale_date"],
    ),
    "fact_expenses": TableConfig(
        display_name="Gastos",
        group="Transacciones",
        columns={
            "date_id": ColSpec("date", True, "2026-03-15"),
            "account_id": ColSpec("int", True, 1),
            "cost_center_id": ColSpec("int", True, 1),
            "description": ColSpec("str", False, "Pago de servicios"),
            "amount": ColSpec("float", True, 5000.0),
            "budget_amount": ColSpec("float", False, 5500.0),
            "variance": ColSpec("float", False, -500.0),
            "variance_pct": ColSpec("float", False, -0.091),
            "category": ColSpec("str", False, "fixed"),
            "is_recurring": ColSpec("bool", False, 1),
            "vendor_id": ColSpec("int", False, 1),
        },
        required_columns=["date_id", "account_id", "cost_center_id", "amount"],
        computed_columns=["variance", "variance_pct"],
        fk_checks={"account_id": "dim_accounts", "cost_center_id": "dim_cost_centers", "vendor_id": "dim_vendors"},
        date_columns=["date_id"],
    ),
    "fact_financials": TableConfig(
        display_name="Estados Financieros",
        group="Transacciones",
        columns={
            "period": ColSpec("str", True, "2026-03"),
            "year": ColSpec("int", False, 2026),
            "month": ColSpec("int", False, 3),
            "statement_type": ColSpec("str", True, "income_statement"),
            "account_id": ColSpec("int", False, 1),
            "account_code": ColSpec("str", False, "4100"),
            "account_name": ColSpec("str", True, "Ingresos por Ventas"),
            "parent_group": ColSpec("str", False, "Ingresos Operacionales"),
            "sub_group": ColSpec("str", False, "Ventas"),
            "amount": ColSpec("float", True, 150000.0),
            "prev_period": ColSpec("float", False, 140000.0),
            "prev_year": ColSpec("float", False, 130000.0),
            "budget": ColSpec("float", False, 155000.0),
            "ytd_actual": ColSpec("float", False, 430000.0),
            "ytd_budget": ColSpec("float", False, 460000.0),
        },
        required_columns=["period", "statement_type", "account_name", "amount"],
        computed_columns=["year", "month"],
        fk_checks={"account_id": "dim_accounts"},
        date_columns=[],
    ),
    "fact_cashflow": TableConfig(
        display_name="Flujo de Caja",
        group="Transacciones",
        columns={
            "date_id": ColSpec("date", True, "2026-03-15"),
            "category": ColSpec("str", True, "operating"),
            "sub_category": ColSpec("str", False, "collections"),
            "description": ColSpec("str", False, "Cobro de facturas"),
            "inflow": ColSpec("float", False, 50000.0),
            "outflow": ColSpec("float", False, 0.0),
            "net_flow": ColSpec("float", False, 50000.0),
            "running_balance": ColSpec("float", False, 250000.0),
            "is_projected": ColSpec("bool", False, 0),
            "confidence": ColSpec("float", False, 1.0),
            "source": ColSpec("str", False, "excel"),
        },
        required_columns=["date_id", "category"],
        computed_columns=["net_flow"],
        fk_checks=None,
        date_columns=["date_id"],
    ),
}

MONTH_NAMES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


# ─── File reading ───────────────────────────────────────────────────

def read_file(file: BinaryIO, filename: str) -> pd.DataFrame:
    """Read an Excel or CSV file into a DataFrame."""
    filename_lower = filename.lower()
    if filename_lower.endswith(".xlsx"):
        df = pd.read_excel(file, engine="openpyxl")
    elif filename_lower.endswith(".csv"):
        raw = file.read()
        file.seek(0)
        try:
            df = pd.read_csv(BytesIO(raw), encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(BytesIO(raw), encoding="latin-1")
    else:
        raise ValueError(f"Formato no soportado: {filename}. Use .xlsx o .csv")

    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]
    logger.info(f"File read: {filename} — {len(df)} rows, {len(df.columns)} columns")
    return df


# ─── Column mapping ─────────────────────────────────────────────────

def normalize_column(name: str) -> str:
    """Normalize a column name for matching."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def auto_map_columns(
    source_cols: list[str], target_table: str
) -> dict[str, str | None]:
    """Auto-map source columns to target table columns by normalized name.

    Returns {target_col: source_col_or_None}.
    """
    config = TABLE_REGISTRY[target_table]
    norm_source = {normalize_column(c): c for c in source_cols}
    mapping: dict[str, str | None] = {}
    for target_col in config.columns:
        norm_target = normalize_column(target_col)
        mapping[target_col] = norm_source.get(norm_target)
    return mapping


def apply_mapping(df: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    """Select and rename columns from source to target names."""
    result = pd.DataFrame()
    for target_col, source_col in mapping.items():
        if source_col and source_col in df.columns:
            result[target_col] = df[source_col]
        # unmapped columns left out — they'll be NULL / use DB defaults
    return result


# ─── Validation ─────────────────────────────────────────────────────

def validate_mapping(
    df: pd.DataFrame, mapping: dict[str, str | None], target_table: str
) -> ValidationResult:
    """Check that all required columns are mapped."""
    config = TABLE_REGISTRY[target_table]
    errors: list[str] = []
    warnings: list[str] = []

    for req_col in config.required_columns:
        src = mapping.get(req_col)
        if not src:
            errors.append(f"Columna requerida '{req_col}' no tiene mapeo asignado.")

    unmapped = [t for t, s in mapping.items() if s is None and t not in (config.computed_columns or [])]
    if unmapped:
        warnings.append(f"Columnas sin mapear (usarán valores por defecto): {', '.join(unmapped)}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_data(
    df: pd.DataFrame, target_table: str
) -> ValidationResult:
    """Validate data types, required values, FK references, and ranges."""
    config = TABLE_REGISTRY[target_table]
    errors: list[str] = []
    warnings: list[str] = []

    if df.empty:
        errors.append("El archivo no contiene datos.")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Required column nulls
    for col in config.required_columns:
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                errors.append(f"'{col}' tiene {null_count} valores vacíos (es requerido).")

    # Type validation
    for col_name, spec in config.columns.items():
        if col_name not in df.columns:
            continue
        series = df[col_name].dropna()
        if series.empty:
            continue

        if spec.dtype == "float":
            non_numeric = pd.to_numeric(series, errors="coerce").isna().sum()
            if non_numeric > 0:
                errors.append(f"'{col_name}' tiene {non_numeric} valores no numéricos.")

        elif spec.dtype == "int":
            non_numeric = pd.to_numeric(series, errors="coerce").isna().sum()
            if non_numeric > 0:
                errors.append(f"'{col_name}' tiene {non_numeric} valores no numéricos.")

        elif spec.dtype == "date":
            bad_dates = pd.to_datetime(series, errors="coerce", dayfirst=True).isna().sum()
            if bad_dates > 0:
                errors.append(f"'{col_name}' tiene {bad_dates} fechas no válidas.")

    # FK reference checks
    if config.fk_checks:
        for col, dim_table in config.fk_checks.items():
            if col not in df.columns:
                continue
            source_ids = set(df[col].dropna().unique())
            if not source_ids:
                continue
            pk_col = _pk_for_dim(dim_table)
            existing = set(
                query_df(f"SELECT {pk_col} FROM {dim_table}")[pk_col].tolist()
            )
            orphans = source_ids - existing
            if orphans:
                sample = list(orphans)[:5]
                errors.append(
                    f"'{col}' tiene {len(orphans)} IDs que no existen en {dim_table}: {sample}"
                )

    # Range checks for common patterns
    for col_name in ["quantity", "qty_on_hand", "original_amount", "amount"]:
        if col_name in df.columns:
            negatives = (pd.to_numeric(df[col_name], errors="coerce") < 0).sum()
            if negatives > 0:
                warnings.append(f"'{col_name}' tiene {negatives} valores negativos.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def _pk_for_dim(dim_table: str) -> str:
    """Return the primary key column name for a dimension table."""
    pk_map = {
        "dim_products": "product_id",
        "dim_customers": "customer_id",
        "dim_vendors": "vendor_id",
        "dim_sellers": "seller_id",
        "dim_accounts": "account_id",
        "dim_cost_centers": "cost_center_id",
    }
    return pk_map[dim_table]


# ─── Computed fields ────────────────────────────────────────────────

def compute_derived_fields(df: pd.DataFrame, target_table: str) -> pd.DataFrame:
    """Fill in derived columns if they are missing or NaN. Never overwrites user values."""
    df = df.copy()

    if target_table == "fact_sales":
        _fill(df, "discount_pct", 0.0)
        _derive(df, "subtotal", lambda: df["quantity"] * df["unit_price"] * (1 - df["discount_pct"]))
        if "unit_cost" in df.columns:
            _derive(df, "cost_total", lambda: df["quantity"] * df["unit_cost"])
            _derive(df, "gross_profit", lambda: df["subtotal"] - df["cost_total"])
            _derive(df, "margin_pct", lambda: (df["gross_profit"] / df["subtotal"]).replace([float("inf"), float("-inf")], 0))
        _derive(df, "tax_amount", lambda: df["subtotal"] * 0.13)
        _derive(df, "total", lambda: df["subtotal"] + df.get("tax_amount", 0))
        _fill(df, "currency", "BOB")
        _fill(df, "status", "posted")

    elif target_table == "fact_receivables":
        _fill(df, "paid_amount", 0.0)
        _derive(df, "balance", lambda: df["original_amount"] - df["paid_amount"])
        _compute_aging(df, "due_date")
        _fill(df, "status", "current")
        # Override status for overdue
        if "due_date" in df.columns and "status" in df.columns:
            due = pd.to_datetime(df["due_date"], errors="coerce")
            overdue_mask = due < pd.Timestamp(date.today())
            balance_mask = df["balance"] > 0
            df.loc[overdue_mask & balance_mask, "status"] = df.loc[
                overdue_mask & balance_mask, "status"
            ].replace("current", "overdue")

    elif target_table == "fact_payables":
        _fill(df, "paid_amount", 0.0)
        _derive(df, "balance", lambda: df["original_amount"] - df["paid_amount"])
        _compute_aging(df, "due_date")
        _fill(df, "currency", "BOB")
        _fill(df, "status", "current")
        # Priority from days_overdue
        if "days_overdue" in df.columns:
            days = pd.to_numeric(df["days_overdue"], errors="coerce").fillna(0)
            priority = pd.Series("normal", index=df.index)
            priority[days > 30] = "high"
            priority[days > 60] = "critical"
            _derive(df, "priority", lambda: priority)

    elif target_table == "fact_inventory":
        _fill(df, "qty_reserved", 0.0)
        _derive(df, "qty_available", lambda: df["qty_on_hand"] - df["qty_reserved"])
        if "unit_cost" in df.columns:
            _derive(df, "total_value", lambda: df["qty_on_hand"] * df["unit_cost"])

    elif target_table == "fact_expenses":
        if "budget_amount" in df.columns:
            _derive(df, "variance", lambda: df["amount"] - df["budget_amount"])
            _derive(
                df, "variance_pct",
                lambda: (df["variance"] / df["budget_amount"].replace(0, 1)),
            )

    elif target_table == "fact_financials":
        if "period" in df.columns:
            _derive(df, "year", lambda: df["period"].str[:4].astype(int))
            _derive(df, "month", lambda: df["period"].str[5:7].astype(int))

    elif target_table == "fact_cashflow":
        _fill(df, "inflow", 0.0)
        _fill(df, "outflow", 0.0)
        _derive(df, "net_flow", lambda: df["inflow"] - df["outflow"])
        _fill(df, "is_projected", 0)
        _fill(df, "source", "excel")

    return df


def _fill(df: pd.DataFrame, col: str, default: Any) -> None:
    """Set column to default if missing or fill NaN values."""
    if col not in df.columns:
        df[col] = default
    else:
        df[col] = df[col].fillna(default)


def _derive(df: pd.DataFrame, col: str, fn: Any) -> None:
    """Compute a column only where it is missing or NaN."""
    if col not in df.columns:
        df[col] = fn()
    else:
        mask = df[col].isna()
        if mask.any():
            computed = fn()
            df.loc[mask, col] = computed[mask] if hasattr(computed, "loc") else computed


def _compute_aging(df: pd.DataFrame, due_col: str) -> None:
    """Compute days_overdue and aging_bucket from a due date column."""
    if due_col not in df.columns:
        return
    due = pd.to_datetime(df[due_col], errors="coerce")
    today = pd.Timestamp(date.today())
    days = (today - due).dt.days.clip(lower=0)
    _derive(df, "days_overdue", lambda: days)

    if "days_overdue" in df.columns:
        d = pd.to_numeric(df["days_overdue"], errors="coerce").fillna(0)
        bucket = pd.Series("current", index=df.index)
        bucket[d > 0] = "1-30"
        bucket[d > 30] = "31-60"
        bucket[d > 60] = "61-90"
        bucket[d > 90] = "90+"
        _derive(df, "aging_bucket", lambda: bucket)


# ─── Date dimension auto-population ────────────────────────────────

def _fiscal_quarter(month: int, fiscal_start: int = 1) -> int:
    adjusted = (month - fiscal_start) % 12
    return adjusted // 3 + 1


def ensure_dim_time(df: pd.DataFrame, date_columns: list[str]) -> int:
    """Insert missing dates into dim_time. Returns count of new rows."""
    all_dates: set[str] = set()
    for col in date_columns:
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], errors="coerce").dropna()
        all_dates.update(parsed.dt.strftime("%Y-%m-%d").tolist())

    if not all_dates:
        return 0

    existing = set(query_df("SELECT date_id FROM dim_time")["date_id"].tolist())
    missing = all_dates - existing
    if not missing:
        return 0

    rows = []
    for date_str in sorted(missing):
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        rows.append({
            "date_id": date_str,
            "date": date_str,
            "day": d.day,
            "month": d.month,
            "month_name": MONTH_NAMES_ES[d.month],
            "quarter": (d.month - 1) // 3 + 1,
            "year": d.year,
            "week_number": d.isocalendar()[1],
            "day_of_week": d.isoweekday(),
            "is_weekend": 1 if d.isoweekday() >= 6 else 0,
            "fiscal_year": d.year,
            "fiscal_quarter": _fiscal_quarter(d.month),
        })

    insert_df(pd.DataFrame(rows), "dim_time", if_exists="append")
    logger.info(f"dim_time: {len(rows)} new dates inserted")
    return len(rows)


# ─── Date normalization ─────────────────────────────────────────────

def normalize_dates(df: pd.DataFrame, target_table: str) -> pd.DataFrame:
    """Convert date columns to YYYY-MM-DD string format."""
    config = TABLE_REGISTRY[target_table]
    df = df.copy()
    for col in config.date_columns:
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
        df[col] = parsed.dt.strftime("%Y-%m-%d")
    return df


# ─── Import execution ──────────────────────────────────────────────

def import_data(
    df: pd.DataFrame, target_table: str, mode: str = "append"
) -> ImportResult:
    """Import a DataFrame into the target table.

    Args:
        df: Mapped and validated DataFrame.
        target_table: Name of the target table.
        mode: "append" to add records, "replace" to delete all existing + load.

    Returns:
        ImportResult with row count and status message.
    """
    config = TABLE_REGISTRY[target_table]

    # Normalize dates to YYYY-MM-DD
    df = normalize_dates(df, target_table)

    # Auto-populate dim_time
    dim_time_added = 0
    if config.date_columns:
        dim_time_added = ensure_dim_time(df, config.date_columns)

    # Compute derived fields
    df = compute_derived_fields(df, target_table)

    # Delete existing data if replacing
    if mode == "replace":
        execute_sql(f"DELETE FROM {target_table}")
        logger.info(f"Deleted all rows from {target_table} (replace mode)")

    # Insert
    rows = insert_df(df, target_table, if_exists="append")
    logger.info(f"Imported {rows} rows into {target_table}")

    return ImportResult(
        rows_inserted=rows,
        dim_time_added=dim_time_added,
        message=f"Se importaron {rows} registros en {config.display_name}.",
    )


# ─── Sync log ──────────────────────────────────────────────────────

def log_import(
    source: str,
    module: str,
    records: int,
    status: str,
    error_message: str | None,
    started_at: datetime,
    completed_at: datetime,
) -> None:
    """Write an entry to the sync_log table."""
    duration = (completed_at - started_at).total_seconds()
    execute_sql(
        """INSERT INTO sync_log (source, module, records_synced, status,
           error_message, started_at, completed_at, duration_sec)
           VALUES (:source, :module, :records, :status, :error,
                   :started, :completed, :duration)""",
        {
            "source": source,
            "module": module,
            "records": records,
            "status": status,
            "error": error_message,
            "started": started_at.isoformat(),
            "completed": completed_at.isoformat(),
            "duration": duration,
        },
    )


def get_import_history(limit: int = 50) -> pd.DataFrame:
    """Return recent import history from sync_log."""
    return query_df(
        "SELECT * FROM sync_log ORDER BY started_at DESC LIMIT :limit",
        {"limit": limit},
    )


# ─── Template generation ───────────────────────────────────────────

def generate_template(target_table: str) -> pd.DataFrame:
    """Generate a 1-row template DataFrame with sample values."""
    config = TABLE_REGISTRY[target_table]
    row = {col: spec.sample for col, spec in config.columns.items()}
    return pd.DataFrame([row])


def get_table_options() -> list[dict[str, str]]:
    """Return grouped table options for the UI selectbox."""
    options = []
    for group_name in ["Dimensiones", "Transacciones"]:
        for table_name, config in TABLE_REGISTRY.items():
            if config.group == group_name:
                options.append({
                    "table": table_name,
                    "label": f"{config.display_name} ({table_name})",
                    "group": group_name,
                })
    return options
