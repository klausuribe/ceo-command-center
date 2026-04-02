"""Expense analytics — budget vs actual, variance, trends."""

from datetime import date

import pandas as pd
from database.db_manager import query_df


def monthly_trend(months: int = 12) -> pd.DataFrame:
    """Monthly expense trend with budget comparison."""
    return query_df(
        "SELECT substr(date_id,1,7) as period, "
        "SUM(amount) as actual, SUM(budget_amount) as budget, "
        "SUM(variance) as variance "
        "FROM fact_expenses "
        "GROUP BY period ORDER BY period DESC LIMIT :n",
        {"n": months}
    )


def by_account(period: str | None = None) -> pd.DataFrame:
    """Expense breakdown by account with budget variance."""
    p = period or f"{date.today().year}-{date.today().month:02d}"
    return query_df(
        "SELECT a.name as account, a.code, e.category, "
        "SUM(e.amount) as actual, SUM(e.budget_amount) as budget, "
        "SUM(e.variance) as variance, "
        "CASE WHEN SUM(e.budget_amount) > 0 "
        "  THEN ROUND(SUM(e.variance) / SUM(e.budget_amount) * 100, 1) "
        "  ELSE 0 END as variance_pct "
        "FROM fact_expenses e "
        "JOIN dim_accounts a ON e.account_id = a.account_id "
        "WHERE e.date_id LIKE :p "
        "GROUP BY e.account_id ORDER BY actual DESC",
        {"p": f"{p}%"}
    )


def by_cost_center(period: str | None = None) -> pd.DataFrame:
    """Expense by cost center with traffic-light status."""
    p = period or f"{date.today().year}-{date.today().month:02d}"
    df = query_df(
        "SELECT cc.name as cost_center, cc.department, cc.responsible, "
        "SUM(e.amount) as actual, SUM(e.budget_amount) as budget, "
        "SUM(e.variance) as variance "
        "FROM fact_expenses e "
        "JOIN dim_cost_centers cc ON e.cost_center_id = cc.cost_center_id "
        "WHERE e.date_id LIKE :p "
        "GROUP BY e.cost_center_id ORDER BY actual DESC",
        {"p": f"{p}%"}
    )
    if df.empty:
        return df
    df["variance_pct"] = (df["variance"] / df["budget"].replace(0, 1) * 100).round(1)
    df["status"] = df["variance_pct"].apply(
        lambda v: "🔴" if v > 10 else ("🟡" if v > 0 else "🟢")
    )
    return df


def fixed_vs_variable(period: str | None = None) -> pd.DataFrame:
    """Breakdown by expense category (fixed/variable/semi-variable)."""
    p = period or f"{date.today().year}-{date.today().month:02d}"
    return query_df(
        "SELECT category, SUM(amount) as actual, SUM(budget_amount) as budget "
        "FROM fact_expenses WHERE date_id LIKE :p GROUP BY category",
        {"p": f"{p}%"}
    )


def anomalies(period: str | None = None, threshold: float = 2.0) -> pd.DataFrame:
    """Detect unusual expenses (>threshold standard deviations from mean)."""
    # Calculate historical mean and std per account
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
        {"p": f"{p}%"}
    )

    if current.empty:
        return current

    merged = current.merge(stats, on="account_id", how="left")
    merged["hist_std"] = pd.to_numeric(merged["hist_std"], errors="coerce").fillna(1).replace(0, 1)
    merged["z_score"] = ((merged["amount"] - merged["hist_mean"]) /
                          merged["hist_std"]).round(2)
    return merged[merged["z_score"].abs() > threshold].sort_values("z_score", ascending=False)


def ytd_budget_consumption() -> pd.DataFrame:
    """Year-to-date budget consumption rate by account."""
    year = date.today().year
    return query_df(
        "SELECT a.name as account, "
        "SUM(e.amount) as ytd_actual, SUM(e.budget_amount) as ytd_budget, "
        "CASE WHEN SUM(e.budget_amount) > 0 "
        "  THEN ROUND(SUM(e.amount) / SUM(e.budget_amount) * 100, 1) "
        "  ELSE 0 END as consumption_pct "
        "FROM fact_expenses e "
        "JOIN dim_accounts a ON e.account_id = a.account_id "
        "WHERE substr(e.date_id,1,4) = :y "
        "GROUP BY e.account_id ORDER BY consumption_pct DESC",
        {"y": str(year)}
    )
