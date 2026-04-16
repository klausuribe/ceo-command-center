"""Expense analytics — budget vs actual, variance, trends.

Budget resolution: un valor de config_budgets por (año, mes, cuenta) gana
sobre la suma de fact_expenses.budget_amount de esas filas. Si no hay override,
cae al fallback denormalizado (compatible con imports de Odoo).

Todas las queries pre-agregan por (año, mes, cuenta) antes de hacer LEFT JOIN
a config_budgets — el join es 1:1 así que el override no se multiplica por la
cantidad de líneas (cost centers) de esa cuenta en ese mes.
"""

from datetime import date

import pandas as pd
from database.db_manager import query_df


# ── CTE reutilizable: una fila por (year, month, account_id) con budget resuelto ──
# Key invariant: LEFT JOIN a config_budgets sobre (year, month, account_id, module)
# es 1:1 gracias al UNIQUE index idx_config_budgets_unique.
_ACCOUNT_MONTH_CTE = """
WITH account_month AS (
    SELECT
        substr(e.date_id, 1, 7) AS period,
        CAST(substr(e.date_id, 1, 4) AS INTEGER) AS year,
        CAST(substr(e.date_id, 6, 2) AS INTEGER) AS month,
        e.account_id,
        SUM(e.amount) AS actual,
        SUM(e.budget_amount) AS fallback_budget
    FROM fact_expenses e
    GROUP BY period, e.account_id
),
resolved AS (
    SELECT
        am.period, am.year, am.month, am.account_id,
        am.actual,
        COALESCE(cb.target_value, am.fallback_budget) AS budget
    FROM account_month am
    LEFT JOIN config_budgets cb
        ON cb.module = 'expenses'
        AND cb.account_id = am.account_id
        AND cb.year = am.year
        AND cb.month = am.month
)
"""


def monthly_trend(months: int = 12) -> pd.DataFrame:
    """Monthly expense trend with budget comparison (override-aware)."""
    return query_df(
        _ACCOUNT_MONTH_CTE +
        "SELECT period, SUM(actual) AS actual, SUM(budget) AS budget, "
        "       SUM(actual - budget) AS variance "
        "FROM resolved "
        "GROUP BY period ORDER BY period DESC LIMIT :n",
        {"n": months},
    )


def by_account(period: str | None = None) -> pd.DataFrame:
    """Expense breakdown by account with budget variance (override-aware)."""
    p = period or f"{date.today().year}-{date.today().month:02d}"
    return query_df(
        _ACCOUNT_MONTH_CTE +
        "SELECT a.name AS account, a.code, "
        "       r.actual, r.budget, "
        "       r.actual - r.budget AS variance, "
        "       CASE WHEN r.budget > 0 "
        "            THEN ROUND((r.actual - r.budget) / r.budget * 100, 1) "
        "            ELSE 0 END AS variance_pct, "
        "       (SELECT category FROM fact_expenses fe WHERE fe.account_id = r.account_id "
        "        AND substr(fe.date_id,1,7) = r.period LIMIT 1) AS category "
        "FROM resolved r "
        "JOIN dim_accounts a ON r.account_id = a.account_id "
        "WHERE r.period = :p "
        "ORDER BY r.actual DESC",
        {"p": p},
    )


def by_cost_center(period: str | None = None) -> pd.DataFrame:
    """Expense by cost center with traffic-light status (override-aware).

    El override está a nivel cuenta. Se prorratea al CC por la proporción real del CC
    dentro de la cuenta en ese mes. Si hay override y actual_cuenta=0, se prorratea
    por cantidad de líneas para no perder el budget.
    """
    p = period or f"{date.today().year}-{date.today().month:02d}"
    year, month = int(p[:4]), int(p[5:7])

    # Raw data por (account, cost_center)
    raw = query_df(
        "SELECT cc.cost_center_id, cc.name AS cost_center, cc.department, cc.responsible, "
        "       e.account_id, "
        "       SUM(e.amount) AS actual, SUM(e.budget_amount) AS fallback_budget, "
        "       COUNT(*) AS n_lines "
        "FROM fact_expenses e "
        "JOIN dim_cost_centers cc ON e.cost_center_id = cc.cost_center_id "
        "WHERE e.date_id LIKE :p "
        "GROUP BY cc.cost_center_id, e.account_id",
        {"p": f"{p}%"},
    )
    if raw.empty:
        return raw

    # Totales por cuenta en el mes (para prorratear)
    account_totals = (
        raw.groupby("account_id")
        .agg(account_actual=("actual", "sum"), account_lines=("n_lines", "sum"))
        .reset_index()
    )

    # Overrides de ese (year, month) por cuenta
    overrides = query_df(
        "SELECT account_id, target_value FROM config_budgets "
        "WHERE module='expenses' AND year=:y AND month=:m",
        {"y": year, "m": month},
    )

    merged = raw.merge(account_totals, on="account_id", how="left")
    merged = merged.merge(overrides, on="account_id", how="left")

    def _budget(row: pd.Series) -> float:
        override = row.get("target_value")
        if pd.isna(override) or override is None:
            return float(row["fallback_budget"] or 0)
        if row["account_actual"] and row["account_actual"] > 0:
            share = row["actual"] / row["account_actual"]
        else:
            share = row["n_lines"] / row["account_lines"] if row["account_lines"] else 0
        return float(override) * float(share)

    merged["budget"] = merged.apply(_budget, axis=1)

    # Sum up to cost center level
    result = (
        merged.groupby(["cost_center_id", "cost_center", "department", "responsible"])
        .agg(actual=("actual", "sum"), budget=("budget", "sum"))
        .reset_index()
        .drop(columns=["cost_center_id"])
    )
    result["variance"] = result["actual"] - result["budget"]
    result["variance_pct"] = (
        result["variance"] / result["budget"].replace(0, 1) * 100
    ).round(1)
    result["status"] = result["variance_pct"].apply(
        lambda v: "🔴" if v > 10 else ("🟡" if v > 0 else "🟢")
    )
    return result.sort_values("actual", ascending=False)


def fixed_vs_variable(period: str | None = None) -> pd.DataFrame:
    """Breakdown by expense category, override-aware.

    La categoría vive en fact_expenses. Se agrega (period, account, category)
    y después se aplica el override por cuenta antes de sumar a category.
    """
    p = period or f"{date.today().year}-{date.today().month:02d}"
    year, month = int(p[:4]), int(p[5:7])

    raw = query_df(
        "SELECT e.category, e.account_id, "
        "       SUM(e.amount) AS actual, SUM(e.budget_amount) AS fallback_budget "
        "FROM fact_expenses e "
        "WHERE e.date_id LIKE :p "
        "GROUP BY e.category, e.account_id",
        {"p": f"{p}%"},
    )
    if raw.empty:
        return raw

    overrides = query_df(
        "SELECT account_id, target_value FROM config_budgets "
        "WHERE module='expenses' AND year=:y AND month=:m",
        {"y": year, "m": month},
    )
    merged = raw.merge(overrides, on="account_id", how="left")
    merged["budget"] = merged["target_value"].astype(float).fillna(
        merged["fallback_budget"].astype(float)
    )

    return (
        merged.groupby("category")
        .agg(actual=("actual", "sum"), budget=("budget", "sum"))
        .reset_index()
    )


def anomalies(period: str | None = None, threshold: float = 2.0) -> pd.DataFrame:
    """Detect unusual expenses (>threshold standard deviations from mean)."""
    df = query_df(
        "SELECT account_id, substr(date_id,1,7) as period, SUM(amount) as amount "
        "FROM fact_expenses GROUP BY account_id, period"
    )
    if df.empty:
        return df

    stats = df.groupby("account_id")["amount"].agg(["mean", "std"]).reset_index()
    stats.columns = ["account_id", "hist_mean", "hist_std"]

    p = period or f"{date.today().year}-{date.today().month:02d}"
    current = query_df(
        "SELECT e.account_id, a.name as account, SUM(e.amount) as amount "
        "FROM fact_expenses e JOIN dim_accounts a ON e.account_id = a.account_id "
        "WHERE e.date_id LIKE :p GROUP BY e.account_id",
        {"p": f"{p}%"},
    )

    if current.empty:
        return current

    merged = current.merge(stats, on="account_id", how="left")
    merged["hist_std"] = pd.to_numeric(merged["hist_std"], errors="coerce").fillna(1).replace(0, 1)
    merged["z_score"] = ((merged["amount"] - merged["hist_mean"]) / merged["hist_std"]).round(2)
    return merged[merged["z_score"].abs() > threshold].sort_values("z_score", ascending=False)


def ytd_budget_consumption() -> pd.DataFrame:
    """Year-to-date budget consumption rate by account (override-aware)."""
    year = date.today().year
    return query_df(
        _ACCOUNT_MONTH_CTE +
        "SELECT a.name AS account, "
        "       SUM(r.actual) AS ytd_actual, "
        "       SUM(r.budget) AS ytd_budget, "
        "       CASE WHEN SUM(r.budget) > 0 "
        "            THEN ROUND(SUM(r.actual) / SUM(r.budget) * 100, 1) "
        "            ELSE 0 END AS consumption_pct "
        "FROM resolved r "
        "JOIN dim_accounts a ON r.account_id = a.account_id "
        "WHERE r.year = :y "
        "GROUP BY r.account_id ORDER BY consumption_pct DESC",
        {"y": year},
    )
