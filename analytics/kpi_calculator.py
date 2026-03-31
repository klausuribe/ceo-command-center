"""Centralized KPI computation across all modules."""

from datetime import date, timedelta

import pandas as pd
from loguru import logger

from database.db_manager import query_df, query_scalar


def _current_period() -> str:
    """Return current period as 'YYYY-MM'."""
    today = date.today()
    return f"{today.year}-{today.month:02d}"


def _prev_period(period: str) -> str:
    """Return the previous month period."""
    y, m = int(period[:4]), int(period[5:])
    if m == 1:
        return f"{y-1}-12"
    return f"{y}-{m-1:02d}"


def _same_period_last_year(period: str) -> str:
    y, m = int(period[:4]), int(period[5:])
    return f"{y-1}-{m:02d}"


def sales_kpis(period: str | None = None) -> dict:
    """Compute sales KPIs for a given period (YYYY-MM)."""
    period = period or _current_period()
    prefix = period  # matches date_id like '2026-03-%'

    current = query_df(
        "SELECT COALESCE(SUM(total),0) as revenue, "
        "COALESCE(SUM(gross_profit),0) as gross_profit, "
        "COALESCE(AVG(margin_pct),0) as avg_margin, "
        "COUNT(DISTINCT invoice_number) as n_invoices, "
        "COUNT(DISTINCT customer_id) as n_customers "
        "FROM fact_sales WHERE date_id LIKE :p AND status='posted'",
        {"p": f"{prefix}%"}
    ).iloc[0].to_dict()

    prev = query_scalar(
        "SELECT COALESCE(SUM(total),0) FROM fact_sales "
        "WHERE date_id LIKE :p AND status='posted'",
        {"p": f"{_prev_period(period)}%"}
    ) or 0

    prev_year = query_scalar(
        "SELECT COALESCE(SUM(total),0) FROM fact_sales "
        "WHERE date_id LIKE :p AND status='posted'",
        {"p": f"{_same_period_last_year(period)}%"}
    ) or 0

    revenue = current["revenue"]
    current["revenue_prev_month"] = prev
    current["revenue_prev_year"] = prev_year
    current["mom_change_pct"] = ((revenue - prev) / prev * 100) if prev else 0
    current["yoy_change_pct"] = ((revenue - prev_year) / prev_year * 100) if prev_year else 0
    current["period"] = period

    # Daily velocity
    today = date.today()
    if period == _current_period():
        days_elapsed = today.day
    else:
        days_elapsed = 30  # approximate
    current["daily_velocity"] = revenue / max(days_elapsed, 1)

    return current


def receivables_kpis() -> dict:
    """Compute accounts receivable KPIs."""
    data = query_df(
        "SELECT COALESCE(SUM(balance),0) as total_balance, "
        "COALESCE(SUM(CASE WHEN status='overdue' THEN balance ELSE 0 END),0) as overdue, "
        "COALESCE(SUM(CASE WHEN aging_bucket='90+' THEN balance ELSE 0 END),0) as over_90, "
        "COUNT(*) as n_open, "
        "COALESCE(AVG(days_overdue),0) as avg_days_overdue "
        "FROM fact_receivables WHERE status != 'paid'"
    ).iloc[0].to_dict()

    # DSO: (total CxC / ventas últimos 30 días) * 30
    sales_30d = query_scalar(
        "SELECT COALESCE(SUM(total),0) FROM fact_sales "
        "WHERE date_id >= :d AND status='posted'",
        {"d": (date.today() - timedelta(days=30)).isoformat()}
    ) or 1
    data["dso"] = round(data["total_balance"] / sales_30d * 30, 1)

    # Aging distribution
    aging = query_df(
        "SELECT aging_bucket, COALESCE(SUM(balance),0) as amount, COUNT(*) as count "
        "FROM fact_receivables WHERE status != 'paid' "
        "GROUP BY aging_bucket"
    )
    data["aging"] = aging.to_dict("records")

    # Concentration: top 5 customers % of total
    top5 = query_scalar(
        "SELECT COALESCE(SUM(bal),0) FROM ("
        "  SELECT customer_id, SUM(balance) as bal "
        "  FROM fact_receivables WHERE status != 'paid' "
        "  GROUP BY customer_id ORDER BY bal DESC LIMIT 5"
        ")"
    ) or 0
    data["top5_concentration_pct"] = round(top5 / data["total_balance"] * 100, 1) if data["total_balance"] else 0

    return data


def payables_kpis() -> dict:
    """Compute accounts payable KPIs."""
    data = query_df(
        "SELECT COALESCE(SUM(balance),0) as total_balance, "
        "COALESCE(SUM(CASE WHEN status='overdue' THEN balance ELSE 0 END),0) as overdue, "
        "COUNT(*) as n_open, "
        "COALESCE(SUM(CASE WHEN priority='critical' THEN balance ELSE 0 END),0) as critical_amount, "
        "COUNT(CASE WHEN priority='critical' THEN 1 END) as critical_count "
        "FROM fact_payables WHERE status != 'paid'"
    ).iloc[0].to_dict()

    # Due in next 7 days
    next_7 = query_scalar(
        "SELECT COALESCE(SUM(balance),0) FROM fact_payables "
        "WHERE status != 'paid' AND due_date BETWEEN :start AND :end",
        {"start": date.today().isoformat(), "end": (date.today() + timedelta(days=7)).isoformat()}
    ) or 0
    data["due_next_7d"] = next_7

    # DPO
    cogs_30d = query_scalar(
        "SELECT COALESCE(SUM(cost_total),0) FROM fact_sales "
        "WHERE date_id >= :d AND status='posted'",
        {"d": (date.today() - timedelta(days=30)).isoformat()}
    ) or 1
    data["dpo"] = round(data["total_balance"] / cogs_30d * 30, 1)

    # Aging distribution
    aging = query_df(
        "SELECT aging_bucket, COALESCE(SUM(balance),0) as amount, COUNT(*) as count "
        "FROM fact_payables WHERE status != 'paid' GROUP BY aging_bucket"
    )
    data["aging"] = aging.to_dict("records")

    return data


def inventory_kpis() -> dict:
    """Compute inventory KPIs."""
    data = query_df(
        "SELECT COALESCE(SUM(total_value),0) as total_value, "
        "COUNT(*) as total_skus, "
        "COALESCE(AVG(days_of_stock),0) as avg_days_stock, "
        "COUNT(CASE WHEN rotation_class='dead_stock' THEN 1 END) as dead_stock_count, "
        "COALESCE(SUM(CASE WHEN rotation_class='dead_stock' THEN total_value ELSE 0 END),0) as dead_stock_value, "
        "COUNT(CASE WHEN qty_available <= reorder_point THEN 1 END) as below_reorder "
        "FROM fact_inventory"
    ).iloc[0].to_dict()

    # ABC distribution
    abc = query_df(
        "SELECT rotation_class, COUNT(*) as count, "
        "COALESCE(SUM(total_value),0) as value "
        "FROM fact_inventory GROUP BY rotation_class"
    )
    data["abc_distribution"] = abc.to_dict("records")

    # Stockout risk: qty_available < 7 days of sales
    data["stockout_risk"] = query_scalar(
        "SELECT COUNT(*) FROM fact_inventory "
        "WHERE days_of_stock < 7 AND rotation_class IN ('A','B')"
    ) or 0

    return data


def expense_kpis(period: str | None = None) -> dict:
    """Compute expense KPIs for a given period."""
    period = period or _current_period()
    data = query_df(
        "SELECT COALESCE(SUM(amount),0) as total_expenses, "
        "COALESCE(SUM(budget_amount),0) as total_budget, "
        "COALESCE(SUM(variance),0) as total_variance "
        "FROM fact_expenses WHERE date_id LIKE :p",
        {"p": f"{period}%"}
    ).iloc[0].to_dict()

    budget = data["total_budget"]
    data["variance_pct"] = round(data["total_variance"] / budget * 100, 1) if budget else 0
    data["period"] = period

    # By category
    by_cat = query_df(
        "SELECT category, COALESCE(SUM(amount),0) as amount, "
        "COALESCE(SUM(budget_amount),0) as budget "
        "FROM fact_expenses WHERE date_id LIKE :p GROUP BY category",
        {"p": f"{period}%"}
    )
    data["by_category"] = by_cat.to_dict("records")

    return data


def financial_kpis(period: str | None = None) -> dict:
    """Compute financial statement KPIs."""
    period = period or _current_period()

    is_data = query_df(
        "SELECT parent_group, sub_group, COALESCE(SUM(amount),0) as amount "
        "FROM fact_financials WHERE period = :p AND statement_type = 'income_statement' "
        "GROUP BY parent_group, sub_group",
        {"p": period}
    )

    bs_data = query_df(
        "SELECT parent_group, sub_group, COALESCE(SUM(amount),0) as amount "
        "FROM fact_financials WHERE period = :p AND statement_type = 'balance_sheet' "
        "GROUP BY parent_group, sub_group",
        {"p": period}
    )

    # Extract key figures from income statement
    revenue = is_data[is_data["parent_group"] == "Ingresos"]["amount"].sum()
    cogs = abs(is_data[is_data["parent_group"] == "Costos"]["amount"].sum())
    opex = abs(is_data[is_data["parent_group"] == "Gastos Operativos"]["amount"].sum())
    fin_exp = abs(is_data[is_data["parent_group"] == "Gastos Financieros"]["amount"].sum())
    taxes = abs(is_data[is_data["parent_group"] == "Impuestos"]["amount"].sum())
    net_income = revenue - cogs - opex - fin_exp - taxes

    gross_profit = revenue - cogs
    ebit = gross_profit - opex
    ebitda = ebit  # simplified (depreciation already in opex)

    # Balance sheet figures
    def bs_sum(group: str) -> float:
        return abs(bs_data[bs_data["parent_group"] == group]["amount"].sum())

    current_assets = bs_sum("Activo Corriente")
    total_assets = current_assets + bs_sum("Activo No Corriente")
    current_liabilities = bs_sum("Pasivo Corriente")
    total_liabilities = current_liabilities + bs_sum("Pasivo No Corriente")
    equity = bs_sum("Patrimonio")

    # Inventory and cash from BS
    inv_val = abs(bs_data[bs_data["sub_group"] == "Inventarios"]["amount"].sum())
    cash = abs(bs_data[bs_data["sub_group"] == "Efectivo"]["amount"].sum())

    return {
        "period": period,
        "revenue": round(revenue, 2),
        "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": round(gross_profit / revenue * 100, 1) if revenue else 0,
        "ebit": round(ebit, 2),
        "ebitda": round(ebitda, 2),
        "ebitda_margin_pct": round(ebitda / revenue * 100, 1) if revenue else 0,
        "net_income": round(net_income, 2),
        "net_margin_pct": round(net_income / revenue * 100, 1) if revenue else 0,
        "operating_margin_pct": round(ebit / revenue * 100, 1) if revenue else 0,
        # Liquidity
        "current_ratio": round(current_assets / current_liabilities, 2) if current_liabilities else 0,
        "quick_ratio": round((current_assets - inv_val) / current_liabilities, 2) if current_liabilities else 0,
        "cash_ratio": round(cash / current_liabilities, 2) if current_liabilities else 0,
        "working_capital": round(current_assets - current_liabilities, 2),
        # Leverage
        "debt_to_equity": round(total_liabilities / equity, 2) if equity else 0,
        "debt_to_assets": round(total_liabilities / total_assets, 2) if total_assets else 0,
        "interest_coverage": round(ebit / fin_exp, 2) if fin_exp else 0,
        # Profitability
        "roa": round(net_income / total_assets * 100, 1) if total_assets else 0,
        "roe": round(net_income / equity * 100, 1) if equity else 0,
        # Totals
        "total_assets": round(total_assets, 2),
        "total_liabilities": round(total_liabilities, 2),
        "equity": round(equity, 2),
    }


def cashflow_kpis() -> dict:
    """Compute cash flow KPIs."""
    today = date.today()
    month_start = date(today.year, today.month, 1).isoformat()

    data = query_df(
        "SELECT COALESCE(SUM(inflow),0) as month_inflow, "
        "COALESCE(SUM(outflow),0) as month_outflow, "
        "COALESCE(SUM(net_flow),0) as month_net "
        "FROM fact_cashflow WHERE date_id >= :d AND is_projected = 0",
        {"d": month_start}
    ).iloc[0].to_dict()

    # Current balance
    data["current_balance"] = query_scalar(
        "SELECT running_balance FROM fact_cashflow "
        "WHERE is_projected = 0 ORDER BY date_id DESC, cashflow_id DESC LIMIT 1"
    ) or 0

    # By category this month
    by_cat = query_df(
        "SELECT category, COALESCE(SUM(inflow),0) as inflow, "
        "COALESCE(SUM(outflow),0) as outflow, COALESCE(SUM(net_flow),0) as net "
        "FROM fact_cashflow WHERE date_id >= :d AND is_projected = 0 "
        "GROUP BY category",
        {"d": month_start}
    )
    data["by_category"] = by_cat.to_dict("records")

    # Average daily net flow (last 30 days)
    avg_net = query_scalar(
        "SELECT AVG(daily_net) FROM ("
        "  SELECT date_id, SUM(net_flow) as daily_net "
        "  FROM fact_cashflow WHERE date_id >= :d AND is_projected = 0 "
        "  GROUP BY date_id"
        ")",
        {"d": (today - timedelta(days=30)).isoformat()}
    ) or 0
    data["avg_daily_net"] = round(avg_net, 2)

    # Runway: days until cash runs out at current burn rate
    if avg_net < 0:
        data["runway_days"] = round(data["current_balance"] / abs(avg_net), 0)
    else:
        data["runway_days"] = None  # cash positive

    return data


def all_kpis(period: str | None = None) -> dict:
    """Compute all KPIs across modules. Used for Morning Briefing."""
    return {
        "sales": sales_kpis(period),
        "receivables": receivables_kpis(),
        "payables": payables_kpis(),
        "inventory": inventory_kpis(),
        "expenses": expense_kpis(period),
        "financial": financial_kpis(period),
        "cashflow": cashflow_kpis(),
    }
