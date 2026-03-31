"""Accounts Payable analytics — aging, DPO, payment prioritization."""

from datetime import date, timedelta

import pandas as pd
from database.db_manager import query_df, query_scalar


def aging_summary() -> pd.DataFrame:
    """Aging buckets summary."""
    bucket_order = ["current", "1-30", "31-60", "61-90", "90+"]
    df = query_df(
        "SELECT aging_bucket, SUM(balance) as amount, COUNT(*) as count "
        "FROM fact_payables WHERE status != 'paid' GROUP BY aging_bucket"
    )
    df["aging_bucket"] = pd.Categorical(df["aging_bucket"], categories=bucket_order, ordered=True)
    return df.sort_values("aging_bucket")


def by_vendor() -> pd.DataFrame:
    """Payables by vendor with priority info."""
    return query_df(
        "SELECT v.name, v.category, v.payment_terms, "
        "SUM(p.balance) as balance, COUNT(*) as n_invoices, "
        "AVG(p.days_overdue) as avg_overdue, "
        "MAX(p.priority) as max_priority "
        "FROM fact_payables p "
        "JOIN dim_vendors v ON p.vendor_id = v.vendor_id "
        "WHERE p.status != 'paid' "
        "GROUP BY p.vendor_id ORDER BY balance DESC"
    )


def payment_priority_matrix() -> pd.DataFrame:
    """Payment prioritization: urgency × amount.

    Priority score considers: days overdue, amount, vendor criticality.
    """
    df = query_df(
        "SELECT p.payable_id, v.name as vendor, p.invoice_number, "
        "p.balance, p.due_date, p.days_overdue, p.priority, "
        "v.lead_time_days, v.category as vendor_type "
        "FROM fact_payables p "
        "JOIN dim_vendors v ON p.vendor_id = v.vendor_id "
        "WHERE p.status != 'paid' ORDER BY p.days_overdue DESC, p.balance DESC"
    )
    if df.empty:
        return df

    # Priority score 0-100
    max_balance = df["balance"].max() or 1
    max_overdue = df["days_overdue"].max() or 1

    df["urgency_score"] = (
        (df["days_overdue"] / max_overdue) * 40 +
        (df["balance"] / max_balance) * 30 +
        df["priority"].map({"critical": 30, "high": 20, "normal": 10, "low": 5}).fillna(10)
    ).round(0).astype(int)

    return df.sort_values("urgency_score", ascending=False)


def upcoming_payments(days: int = 30) -> pd.DataFrame:
    """Payments due in the next N days."""
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=days)).isoformat()
    return query_df(
        "SELECT p.invoice_number, v.name as vendor, p.due_date, "
        "p.balance, p.priority "
        "FROM fact_payables p "
        "JOIN dim_vendors v ON p.vendor_id = v.vendor_id "
        "WHERE p.status != 'paid' AND p.due_date BETWEEN :start AND :end "
        "ORDER BY p.due_date",
        {"start": today, "end": end}
    )


def cash_vs_payables() -> dict:
    """Compare available cash with upcoming payables."""
    cash = query_scalar(
        "SELECT running_balance FROM fact_cashflow "
        "WHERE is_projected = 0 ORDER BY date_id DESC, cashflow_id DESC LIMIT 1"
    ) or 0

    due_7d = query_scalar(
        "SELECT COALESCE(SUM(balance),0) FROM fact_payables "
        "WHERE status != 'paid' AND due_date <= :d",
        {"d": (date.today() + timedelta(days=7)).isoformat()}
    ) or 0

    due_30d = query_scalar(
        "SELECT COALESCE(SUM(balance),0) FROM fact_payables "
        "WHERE status != 'paid' AND due_date <= :d",
        {"d": (date.today() + timedelta(days=30)).isoformat()}
    ) or 0

    total_open = query_scalar(
        "SELECT COALESCE(SUM(balance),0) FROM fact_payables WHERE status != 'paid'"
    ) or 0

    return {
        "cash_available": cash,
        "due_7d": due_7d,
        "due_30d": due_30d,
        "total_open": total_open,
        "coverage_7d": cash >= due_7d,
        "coverage_30d": cash >= due_30d,
        "gap_30d": max(0, due_30d - cash),
    }


def dpo_by_vendor() -> pd.DataFrame:
    """Days Payable Outstanding per vendor."""
    return query_df(
        "SELECT v.name, v.payment_terms, "
        "AVG(p.days_overdue) as avg_dpo, "
        "SUM(p.balance) as balance, COUNT(*) as n_invoices "
        "FROM fact_payables p "
        "JOIN dim_vendors v ON p.vendor_id = v.vendor_id "
        "WHERE p.status != 'paid' "
        "GROUP BY p.vendor_id ORDER BY avg_dpo DESC"
    )
