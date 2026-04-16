"""Budget projector — proyecta presupuesto de gastos desde históricos y
aplica supuestos estructurados almacenados en config_assumptions.

Granularidad: (year, month, account_id) con module='expenses'.
Fuente de verdad: tabla config_budgets (UPSERT). El analítico hace
COALESCE contra fact_expenses.budget_amount para mantener compatibilidad.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

import numpy as np
import pandas as pd
from loguru import logger

from database.db_manager import execute_sql, query_df


MODULE_EXPENSES = "expenses"
DEFAULT_LOOKBACK = 6


@dataclass(frozen=True)
class BudgetCell:
    """Presupuesto para una cuenta en un mes específico."""
    year: int
    month: int
    account_id: int
    account_name: str
    target_value: float
    source: str          # 'manual' | 'projected' | 'imported'
    notes: str | None = None


def _iter_future_months(start: tuple[int, int], months_ahead: int) -> Iterable[tuple[int, int]]:
    """Genera (año, mes) a partir de start por months_ahead meses inclusive del primero."""
    y, m = start
    for _ in range(months_ahead):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def _history_by_account(account_id: int, lookback: int) -> pd.Series:
    """Serie mensual de gastos actuales para una cuenta, últimos N meses."""
    df = query_df(
        "SELECT substr(date_id,1,7) AS period, SUM(amount) AS amount "
        "FROM fact_expenses WHERE account_id = :aid "
        "GROUP BY period ORDER BY period DESC LIMIT :n",
        {"aid": account_id, "n": lookback},
    )
    if df.empty:
        return pd.Series(dtype=float)
    return df.sort_values("period")["amount"].astype(float).reset_index(drop=True)


def _project_series(series: pd.Series, periods_ahead: int) -> list[float]:
    """Media + tendencia lineal extrapolada N meses adelante.

    Fallback defensivo si hay poca historia: usa la media simple.
    """
    if series.empty:
        return [0.0] * periods_ahead
    if len(series) < 3:
        mean = float(series.mean())
        return [round(mean, 2)] * periods_ahead

    window = min(len(series), DEFAULT_LOOKBACK)
    recent = series.tail(window)
    x = np.arange(len(recent))
    slope, intercept = np.polyfit(x, recent.values, 1)
    base = float(recent.mean())

    out: list[float] = []
    for i in range(1, periods_ahead + 1):
        value = base + slope * i
        out.append(round(max(value, 0.0), 2))
    return out


def _expense_accounts() -> pd.DataFrame:
    """Cuentas de tipo gasto (account_type='expense')."""
    return query_df(
        "SELECT account_id, code, name FROM dim_accounts "
        "WHERE account_type = 'expense' ORDER BY code"
    )


def active_assumptions() -> pd.DataFrame:
    """Supuestos estructurados activos para el módulo de gastos."""
    return query_df(
        "SELECT assumption_id, description, impact_type, impact_value, impact_pct, "
        "       start_date, end_date, category "
        "FROM config_assumptions "
        "WHERE module = :m AND is_active = 1",
        {"m": MODULE_EXPENSES},
    )


def _assumption_multiplier(
    assumptions: pd.DataFrame,
    year: int,
    month: int,
    account_name: str,
) -> tuple[float, float]:
    """Devuelve (multiplier, absolute_delta) a aplicar sobre el base projectado.

    Reglas:
    - impact_type='increase'/'decrease' con impact_pct → multiplier
    - impact_type='replace' con impact_value → reemplaza el base (devuelve (0, impact_value))
    - Filtro por ventana [start_date, end_date] cuando existe
    - Filtro por category: si la fila trae category y matchea el nombre de cuenta (case insensitive substring)
    """
    if assumptions.empty:
        return 1.0, 0.0

    period_first = date(year, month, 1)
    multiplier = 1.0
    absolute = 0.0
    replace_value: float | None = None

    for row in assumptions.to_dict("records"):
        start = row.get("start_date")
        end = row.get("end_date")
        if start and pd.to_datetime(start).date() > period_first:
            continue
        if end and pd.to_datetime(end).date() < period_first:
            continue

        cat = (row.get("category") or "").strip().lower()
        if cat and cat not in account_name.lower():
            continue

        impact_type = (row.get("impact_type") or "").lower()
        pct = row.get("impact_pct")
        value = row.get("impact_value")

        if impact_type == "replace" and value is not None:
            replace_value = float(value)
        elif impact_type == "increase" and pct is not None:
            multiplier *= 1.0 + float(pct) / 100.0
        elif impact_type == "decrease" and pct is not None:
            multiplier *= 1.0 - float(pct) / 100.0
        elif impact_type in ("increase", "decrease") and value is not None:
            sign = 1.0 if impact_type == "increase" else -1.0
            absolute += sign * float(value)

    if replace_value is not None:
        return 0.0, replace_value
    return multiplier, absolute


def project_account_budget(
    account_id: int,
    year: int,
    month: int,
    lookback: int = DEFAULT_LOOKBACK,
) -> float:
    """Proyecta el presupuesto de UNA cuenta para UN mes aplicando supuestos."""
    history = _history_by_account(account_id, lookback)
    offset = _months_between_last_history_and(year, month, history)
    base_series = _project_series(history, max(offset, 1))
    base_value = base_series[-1] if base_series else 0.0

    accounts = _expense_accounts()
    name_row = accounts[accounts["account_id"] == account_id]
    account_name = str(name_row["name"].iloc[0]) if not name_row.empty else ""

    multiplier, absolute = _assumption_multiplier(active_assumptions(), year, month, account_name)
    projected = base_value * multiplier + absolute
    return round(max(projected, 0.0), 2)


def _months_between_last_history_and(year: int, month: int, history: pd.Series) -> int:
    """Cuántos meses hacia adelante proyectar desde el último dato real."""
    df = query_df(
        "SELECT MAX(substr(date_id,1,7)) AS last_period FROM fact_expenses"
    )
    last = df["last_period"].iloc[0] if not df.empty else None
    if not last:
        return 1
    last_year, last_month = int(last[:4]), int(last[5:7])
    return max(1, (year - last_year) * 12 + (month - last_month))


def project_all_accounts(
    start_year: int,
    start_month: int,
    months_ahead: int = 12,
    lookback: int = DEFAULT_LOOKBACK,
) -> pd.DataFrame:
    """Proyecta todas las cuentas de gasto para N meses desde start.

    No persiste. Devuelve DataFrame con columnas:
    year, month, account_id, account_name, target_value, source='projected'.
    """
    accounts = _expense_accounts()
    if accounts.empty:
        return pd.DataFrame(columns=["year", "month", "account_id", "account_name", "target_value", "source"])

    assumptions = active_assumptions()
    rows: list[dict] = []

    for acc in accounts.to_dict("records"):
        acc_id = int(acc["account_id"])
        acc_name = str(acc["name"])
        history = _history_by_account(acc_id, lookback)
        projected = _project_series(history, months_ahead)

        for idx, (y, m) in enumerate(_iter_future_months((start_year, start_month), months_ahead)):
            base = projected[idx] if idx < len(projected) else projected[-1]
            multiplier, absolute = _assumption_multiplier(assumptions, y, m, acc_name)
            value = base * multiplier + absolute
            rows.append({
                "year": y,
                "month": m,
                "account_id": acc_id,
                "account_name": acc_name,
                "target_value": round(max(value, 0.0), 2),
                "source": "projected",
            })

    return pd.DataFrame(rows)


def save_budget(
    year: int,
    month: int,
    account_id: int,
    target_value: float,
    source: str = "manual",
    notes: str | None = None,
) -> None:
    """UPSERT de un presupuesto puntual en config_budgets."""
    account_row = query_df(
        "SELECT name FROM dim_accounts WHERE account_id = :aid",
        {"aid": account_id},
    )
    metric = str(account_row["name"].iloc[0]) if not account_row.empty else f"account_{account_id}"

    execute_sql(
        "INSERT INTO config_budgets "
        "(year, month, module, account_id, metric, target_value, source, notes, updated_at) "
        "VALUES (:y, :m, :mod, :aid, :metric, :val, :src, :notes, CURRENT_TIMESTAMP) "
        "ON CONFLICT(year, month, module, account_id) DO UPDATE SET "
        "  target_value = excluded.target_value, "
        "  source = excluded.source, "
        "  notes = excluded.notes, "
        "  updated_at = CURRENT_TIMESTAMP",
        {
            "y": year, "m": month, "mod": MODULE_EXPENSES,
            "aid": account_id, "metric": metric,
            "val": float(target_value), "src": source, "notes": notes,
        },
    )


def save_many(rows: pd.DataFrame) -> int:
    """Persiste un DataFrame de presupuestos. Ignora filas con target_value nulo o <= 0."""
    if rows.empty:
        return 0
    count = 0
    for r in rows.to_dict("records"):
        value = r.get("target_value")
        if value is None or pd.isna(value):
            continue
        save_budget(
            year=int(r["year"]),
            month=int(r["month"]),
            account_id=int(r["account_id"]),
            target_value=float(value),
            source=str(r.get("source", "manual")),
            notes=r.get("notes"),
        )
        count += 1
    logger.info(f"Persisted {count} budget rows to config_budgets")
    return count


def delete_budget(year: int, month: int, account_id: int) -> None:
    """Borra el override de una celda para volver al fallback de fact_expenses.budget_amount."""
    execute_sql(
        "DELETE FROM config_budgets "
        "WHERE year=:y AND month=:m AND module=:mod AND account_id=:aid",
        {"y": year, "m": month, "mod": MODULE_EXPENSES, "aid": account_id},
    )


def budgets_grid(year: int) -> pd.DataFrame:
    """Grilla edición: filas=cuentas, columnas=meses (1-12). Celdas vacías = usar fallback.

    Devuelve DataFrame indexado por account con columnas account_id, account_name,
    code y una columna por mes (1..12) con el valor actual de config_budgets
    (o NaN si no hay override).
    """
    accounts = _expense_accounts()
    if accounts.empty:
        return pd.DataFrame()

    overrides = query_df(
        "SELECT account_id, month, target_value FROM config_budgets "
        "WHERE year = :y AND module = :mod",
        {"y": year, "mod": MODULE_EXPENSES},
    )

    grid = accounts.rename(columns={"name": "account_name"}).copy()
    for m in range(1, 13):
        grid[str(m)] = np.nan

    for row in overrides.to_dict("records"):
        mask = grid["account_id"] == row["account_id"]
        grid.loc[mask, str(int(row["month"]))] = float(row["target_value"])

    return grid
