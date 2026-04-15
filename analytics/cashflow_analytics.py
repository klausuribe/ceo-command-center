"""Cash flow analytics — patterns, projections, runway."""

from datetime import date, timedelta

import pandas as pd
import numpy as np
from database.db_manager import query_df, query_scalar


def daily_balance(days: int = 30) -> pd.DataFrame:
    """Running balance for the last N days."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    return query_df(
        "SELECT date_id, SUM(inflow) as inflow, SUM(outflow) as outflow, "
        "SUM(net_flow) as net_flow, MAX(running_balance) as balance "
        "FROM fact_cashflow "
        "WHERE date_id >= :d AND is_projected = 0 "
        "GROUP BY date_id ORDER BY date_id",
        {"d": cutoff}
    )


def monthly_summary(months: int = 12) -> pd.DataFrame:
    """Monthly cash flow summary."""
    return query_df(
        "SELECT substr(date_id,1,7) as period, "
        "SUM(inflow) as inflow, SUM(outflow) as outflow, "
        "SUM(net_flow) as net_flow "
        "FROM fact_cashflow WHERE is_projected = 0 "
        "GROUP BY period ORDER BY period DESC LIMIT :n",
        {"n": months}
    )


def by_category(period: str | None = None) -> pd.DataFrame:
    """Cash flow by category and subcategory."""
    p = period or f"{date.today().year}-{date.today().month:02d}"
    return query_df(
        "SELECT category, sub_category, "
        "SUM(inflow) as inflow, SUM(outflow) as outflow, "
        "SUM(net_flow) as net_flow "
        "FROM fact_cashflow WHERE date_id LIKE :p AND is_projected = 0 "
        "GROUP BY category, sub_category "
        "ORDER BY category, net_flow DESC",
        {"p": f"{p}%"}
    )


def waterfall_monthly(period: str | None = None) -> pd.DataFrame:
    """Waterfall data: opening balance + flows by subcategory + closing."""
    p = period or f"{date.today().year}-{date.today().month:02d}"

    # Opening balance: last balance from previous month
    prev_month = _prev_month(p)
    opening = query_scalar(
        "SELECT MAX(running_balance) FROM fact_cashflow "
        "WHERE date_id LIKE :p AND is_projected = 0",
        {"p": f"{prev_month}%"}
    ) or 0

    flows = query_df(
        "SELECT sub_category as item, "
        "SUM(net_flow) as amount "
        "FROM fact_cashflow WHERE date_id LIKE :p AND is_projected = 0 "
        "GROUP BY sub_category ORDER BY amount DESC",
        {"p": f"{p}%"}
    )

    rows = [{"item": "Saldo Inicial", "amount": opening}]
    for _, row in flows.iterrows():
        rows.append({"item": row["item"], "amount": row["amount"]})
    closing = opening + flows["amount"].sum()
    rows.append({"item": "Saldo Final", "amount": closing})

    return pd.DataFrame(rows)


def seasonal_pattern() -> pd.DataFrame:
    """Average cash flow by month (seasonal pattern)."""
    return query_df(
        "SELECT CAST(substr(date_id,6,2) AS INTEGER) as month, "
        "AVG(daily_inflow) as avg_inflow, AVG(daily_outflow) as avg_outflow, "
        "AVG(daily_net) as avg_net "
        "FROM ("
        "  SELECT date_id, SUM(inflow) as daily_inflow, "
        "  SUM(outflow) as daily_outflow, SUM(net_flow) as daily_net "
        "  FROM fact_cashflow WHERE is_projected = 0 "
        "  GROUP BY date_id"
        ") GROUP BY month ORDER BY month"
    )


def projection(days: int = 90) -> pd.DataFrame:
    """Simple cash flow projection based on moving averages.

    Uses 30-day moving average of daily inflows and outflows,
    adjusted by day-of-week patterns.
    """
    # Get last 60 days of actuals for pattern detection
    hist = query_df(
        "SELECT date_id, SUM(inflow) as inflow, SUM(outflow) as outflow "
        "FROM fact_cashflow WHERE is_projected = 0 "
        "AND date_id >= :d GROUP BY date_id ORDER BY date_id",
        {"d": (date.today() - timedelta(days=60)).isoformat()}
    )
    if hist.empty:
        return pd.DataFrame()

    avg_inflow = hist["inflow"].mean()
    avg_outflow = hist["outflow"].mean()
    std_inflow = float(hist["inflow"].std() or 0) if len(hist) > 1 else 0.0
    std_outflow = float(hist["outflow"].std() or 0) if len(hist) > 1 else 0.0

    current_balance = query_scalar(
        "SELECT running_balance FROM fact_cashflow "
        "WHERE is_projected = 0 ORDER BY date_id DESC, cashflow_id DESC LIMIT 1"
    ) or 0

    rows = []
    balance = current_balance
    day_count = 0

    for i in range(1, days * 2):  # Iterate enough calendar days to get 'days' weekdays
        d = date.today() + timedelta(days=i)
        if d.isoweekday() > 5:  # Skip weekends
            continue

        day_count += 1
        if day_count > days:
            break

        # Base projection with small random variation for scenarios
        inflow = max(0, avg_inflow)
        outflow = max(0, avg_outflow)

        # Payroll spikes on 1st-5th and 25th-31st
        if d.day <= 5 or d.day >= 25:
            outflow *= 1.3

        net = inflow - outflow
        balance += net

        rows.append({
            "date_id": d.isoformat(),
            "inflow": round(inflow, 2),
            "outflow": round(outflow, 2),
            "net_flow": round(net, 2),
            "balance_base": round(balance, 2),
            "balance_optimistic": round(balance + day_count * std_inflow * 0.3, 2),
            "balance_pessimistic": round(balance - day_count * std_outflow * 0.3, 2),
            "is_projected": 1,
        })

    return pd.DataFrame(rows)


def breakeven_days() -> int | None:
    """Estimate days until cash runs out at current burn rate.

    Returns None if cash positive.
    """
    proj = projection(180)
    if proj.empty:
        return None

    negative = proj[proj["balance_base"] <= 0]
    if negative.empty:
        return None

    first_negative = negative.iloc[0]
    days = (pd.to_datetime(first_negative["date_id"]) - pd.to_datetime(date.today())).days
    return int(days)


def _prev_month(period: str) -> str:
    p = period[:7]  # Handle both YYYY-MM and YYYY-MM-DD
    y, m = int(p[:4]), int(p[5:])
    if m == 1:
        return f"{y-1}-12"
    return f"{y}-{m-1:02d}"
