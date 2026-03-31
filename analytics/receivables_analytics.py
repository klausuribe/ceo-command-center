"""Accounts Receivable analytics — aging, DSO, credit scoring."""

from datetime import date, timedelta

import pandas as pd
from database.db_manager import query_df, query_scalar


def aging_summary() -> pd.DataFrame:
    """Aging buckets summary with amounts and counts."""
    bucket_order = ["current", "1-30", "31-60", "61-90", "90+"]
    df = query_df(
        "SELECT aging_bucket, SUM(balance) as amount, COUNT(*) as count, "
        "SUM(original_amount) as original "
        "FROM fact_receivables WHERE status != 'paid' "
        "GROUP BY aging_bucket"
    )
    df["aging_bucket"] = pd.Categorical(df["aging_bucket"], categories=bucket_order, ordered=True)
    return df.sort_values("aging_bucket")


def aging_by_customer() -> pd.DataFrame:
    """Aging detail by customer — for drill-down."""
    return query_df(
        "SELECT c.name, c.segment, c.city, r.aging_bucket, "
        "SUM(r.balance) as balance, COUNT(*) as n_invoices, "
        "MAX(r.days_overdue) as max_days_overdue "
        "FROM fact_receivables r "
        "JOIN dim_customers c ON r.customer_id = c.customer_id "
        "WHERE r.status != 'paid' "
        "GROUP BY r.customer_id, r.aging_bucket "
        "ORDER BY balance DESC"
    )


def top_debtors(n: int = 10) -> pd.DataFrame:
    """Top N customers by outstanding balance."""
    return query_df(
        "SELECT c.name, c.segment, c.payment_terms, "
        "SUM(r.balance) as balance, SUM(r.original_amount) as original, "
        "COUNT(*) as n_invoices, AVG(r.days_overdue) as avg_days_overdue, "
        "MAX(r.days_overdue) as max_days_overdue "
        "FROM fact_receivables r "
        "JOIN dim_customers c ON r.customer_id = c.customer_id "
        "WHERE r.status != 'paid' "
        "GROUP BY r.customer_id ORDER BY balance DESC LIMIT :n",
        {"n": n}
    )


def dso_by_customer() -> pd.DataFrame:
    """DSO per customer."""
    return query_df(
        "SELECT c.name, c.segment, "
        "AVG(r.days_overdue) as avg_days_overdue, "
        "SUM(r.balance) as balance, COUNT(*) as n_invoices "
        "FROM fact_receivables r "
        "JOIN dim_customers c ON r.customer_id = c.customer_id "
        "WHERE r.status != 'paid' "
        "GROUP BY r.customer_id ORDER BY avg_days_overdue DESC"
    )


def credit_score() -> pd.DataFrame:
    """Simple credit score per customer based on payment behavior.

    Score 0-100: higher = better payer.
    Factors: % paid on time, avg overdue days, current balance ratio.
    """
    df = query_df(
        "SELECT r.customer_id, c.name, c.segment, c.credit_limit, "
        "COUNT(*) as total_invoices, "
        "SUM(CASE WHEN r.days_overdue = 0 THEN 1 ELSE 0 END) as on_time, "
        "AVG(r.days_overdue) as avg_overdue, "
        "SUM(r.balance) as total_balance, "
        "SUM(r.original_amount) as total_original "
        "FROM fact_receivables r "
        "JOIN dim_customers c ON r.customer_id = c.customer_id "
        "GROUP BY r.customer_id"
    )
    if df.empty:
        return df

    df["on_time_pct"] = df["on_time"] / df["total_invoices"]
    df["paid_pct"] = 1 - (df["total_balance"] / df["total_original"].replace(0, 1))

    # Score: weighted formula
    df["score"] = (
        df["on_time_pct"] * 40 +
        df["paid_pct"] * 30 +
        (1 - (df["avg_overdue"].clip(upper=120) / 120)) * 30
    ).round(0).astype(int)

    df["risk_level"] = df["score"].apply(
        lambda s: "Bajo" if s >= 70 else ("Medio" if s >= 40 else "Alto")
    )
    return df.sort_values("score", ascending=False)


def upcoming_due(days: int = 7) -> pd.DataFrame:
    """Invoices due within the next N days — for preventive collection."""
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=days)).isoformat()
    return query_df(
        "SELECT r.invoice_number, c.name as customer, r.due_date, "
        "r.balance, r.original_amount, r.aging_bucket "
        "FROM fact_receivables r "
        "JOIN dim_customers c ON r.customer_id = c.customer_id "
        "WHERE r.status = 'current' AND r.due_date BETWEEN :start AND :end "
        "ORDER BY r.due_date",
        {"start": today, "end": end}
    )


def collection_rate_trend(months: int = 12) -> pd.DataFrame:
    """Monthly collection rate (paid / total original)."""
    return query_df(
        "SELECT substr(date_id,1,7) as period, "
        "SUM(paid_amount) as collected, "
        "SUM(original_amount) as billed, "
        "CASE WHEN SUM(original_amount) > 0 "
        "  THEN ROUND(SUM(paid_amount) / SUM(original_amount) * 100, 1) "
        "  ELSE 0 END as rate_pct "
        "FROM fact_receivables "
        "GROUP BY period ORDER BY period DESC LIMIT :n",
        {"n": months}
    )
