"""Financial analytics — ratios, P&L, balance sheet, trends."""

from datetime import date

import pandas as pd
from database.db_manager import query_df
from analytics.kpi_calculator import financial_kpis


def income_statement(period: str | None = None) -> pd.DataFrame:
    """Structured income statement for a period."""
    p = period or f"{date.today().year}-{date.today().month:02d}"
    return query_df(
        "SELECT account_code, account_name, parent_group, sub_group, "
        "amount, prev_period, prev_year, budget "
        "FROM fact_financials "
        "WHERE period = :p AND statement_type = 'income_statement' "
        "ORDER BY account_code",
        {"p": p}
    )


def balance_sheet(period: str | None = None) -> pd.DataFrame:
    """Structured balance sheet for a period."""
    p = period or f"{date.today().year}-{date.today().month:02d}"
    return query_df(
        "SELECT account_code, account_name, parent_group, sub_group, "
        "amount, prev_period, prev_year, budget "
        "FROM fact_financials "
        "WHERE period = :p AND statement_type = 'balance_sheet' "
        "ORDER BY account_code",
        {"p": p}
    )


def common_size_analysis(period: str | None = None) -> pd.DataFrame:
    """Common-size income statement (% of revenue)."""
    is_df = income_statement(period)
    if is_df.empty:
        return is_df
    revenue = is_df[is_df["parent_group"] == "Ingresos"]["amount"].sum()
    if revenue == 0:
        return is_df
    is_df["pct_of_revenue"] = (is_df["amount"] / revenue * 100).round(1)
    return is_df


def ratios_trend(months: int = 12) -> pd.DataFrame:
    """Key financial ratios over time."""
    periods = query_df(
        "SELECT DISTINCT period FROM fact_financials "
        "ORDER BY period DESC LIMIT :n",
        {"n": months}
    )["period"].tolist()

    rows = []
    for p in periods:
        kpis = financial_kpis(p)
        rows.append(kpis)
    return pd.DataFrame(rows)


def margin_trend(months: int = 12) -> pd.DataFrame:
    """Margin trends (gross, operating, net) over time."""
    df = ratios_trend(months)
    if df.empty:
        return df
    return df[["period", "gross_margin_pct", "operating_margin_pct",
               "net_margin_pct", "ebitda_margin_pct"]].sort_values("period")


def liquidity_trend(months: int = 12) -> pd.DataFrame:
    """Liquidity ratios over time."""
    df = ratios_trend(months)
    if df.empty:
        return df
    return df[["period", "current_ratio", "quick_ratio", "cash_ratio",
               "working_capital"]].sort_values("period")


def leverage_trend(months: int = 12) -> pd.DataFrame:
    """Leverage ratios over time."""
    df = ratios_trend(months)
    if df.empty:
        return df
    return df[["period", "debt_to_equity", "debt_to_assets",
               "interest_coverage"]].sort_values("period")


def efficiency_ratios(period: str | None = None) -> dict:
    """Efficiency ratios: DSO, DPO, DIO, CCC."""
    from analytics.kpi_calculator import receivables_kpis, payables_kpis, inventory_kpis

    rx = receivables_kpis()
    px = payables_kpis()
    ix = inventory_kpis()

    dso = rx.get("dso", 0)
    dpo = px.get("dpo", 0)
    dio = ix.get("avg_days_stock", 0)
    ccc = dso + dio - dpo

    return {
        "dso": round(dso, 1),
        "dpo": round(dpo, 1),
        "dio": round(dio, 1),
        "ccc": round(ccc, 1),
        "interpretation": (
            "Eficiente" if ccc < 30 else
            "Normal" if ccc < 60 else
            "Lento — capital atrapado"
        ),
    }


def period_comparison(period1: str, period2: str) -> pd.DataFrame:
    """Compare two periods side-by-side."""
    p1 = income_statement(period1)
    p2 = income_statement(period2)
    if p1.empty or p2.empty:
        return pd.DataFrame()

    merged = p1[["account_name", "parent_group", "amount"]].rename(
        columns={"amount": f"amount_{period1}"}
    ).merge(
        p2[["account_name", "amount"]].rename(columns={"amount": f"amount_{period2}"}),
        on="account_name", how="outer"
    ).fillna(0)

    merged["change"] = merged[f"amount_{period1}"] - merged[f"amount_{period2}"]
    merged["change_pct"] = (
        merged["change"] / merged[f"amount_{period2}"].replace(0, 1) * 100
    ).round(1)
    return merged
