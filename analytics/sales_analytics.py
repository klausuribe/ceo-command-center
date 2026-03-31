"""Sales analytics — revenue, margins, rankings, Pareto, RFM."""

from datetime import date, timedelta

import pandas as pd
from database.db_manager import query_df


def monthly_trend(months: int = 12) -> pd.DataFrame:
    """Monthly revenue trend with MoM and YoY comparisons."""
    return query_df(
        "SELECT substr(date_id,1,7) as period, "
        "SUM(total) as revenue, SUM(gross_profit) as gross_profit, "
        "AVG(margin_pct) as avg_margin, "
        "COUNT(DISTINCT invoice_number) as n_invoices, "
        "COUNT(DISTINCT customer_id) as n_customers "
        "FROM fact_sales WHERE status='posted' "
        "GROUP BY period ORDER BY period DESC LIMIT :n",
        {"n": months}
    )


def by_category() -> pd.DataFrame:
    """Revenue and margin breakdown by product category."""
    return query_df(
        "SELECT p.category, SUM(s.total) as revenue, "
        "SUM(s.gross_profit) as gross_profit, "
        "AVG(s.margin_pct) as avg_margin, "
        "COUNT(DISTINCT s.invoice_number) as n_invoices "
        "FROM fact_sales s JOIN dim_products p ON s.product_id = p.product_id "
        "WHERE s.status='posted' "
        "GROUP BY p.category ORDER BY revenue DESC"
    )


def by_product_line() -> pd.DataFrame:
    """Revenue breakdown by product line."""
    return query_df(
        "SELECT p.category, p.product_line, SUM(s.total) as revenue, "
        "SUM(s.gross_profit) as gross_profit, AVG(s.margin_pct) as avg_margin, "
        "SUM(s.quantity) as units_sold "
        "FROM fact_sales s JOIN dim_products p ON s.product_id = p.product_id "
        "WHERE s.status='posted' "
        "GROUP BY p.category, p.product_line ORDER BY revenue DESC"
    )


def pareto_products(period: str | None = None) -> pd.DataFrame:
    """Pareto (80/20) analysis — products ranked by revenue with cumulative %."""
    where = "WHERE s.status='posted'"
    params = {}
    if period:
        where += " AND s.date_id LIKE :p"
        params["p"] = f"{period}%"

    df = query_df(
        f"SELECT p.name, p.category, p.product_line, "
        f"SUM(s.total) as revenue, SUM(s.gross_profit) as gross_profit, "
        f"SUM(s.quantity) as units "
        f"FROM fact_sales s JOIN dim_products p ON s.product_id = p.product_id "
        f"{where} GROUP BY s.product_id ORDER BY revenue DESC",
        params
    )
    if df.empty:
        return df
    total = df["revenue"].sum()
    df["pct"] = df["revenue"] / total * 100
    df["cumulative_pct"] = df["pct"].cumsum()
    df["pareto_class"] = df["cumulative_pct"].apply(
        lambda x: "A (80%)" if x <= 80 else ("B (95%)" if x <= 95 else "C")
    )
    return df


def top_products(n: int = 10, by: str = "revenue", period: str | None = None) -> pd.DataFrame:
    """Top N products by revenue, margin, or units."""
    col_map = {"revenue": "SUM(s.total)", "margin": "AVG(s.margin_pct)", "units": "SUM(s.quantity)"}
    order_col = col_map.get(by, "SUM(s.total)")

    where = "WHERE s.status='posted'"
    params: dict = {"n": n}
    if period:
        where += " AND s.date_id LIKE :p"
        params["p"] = f"{period}%"

    return query_df(
        f"SELECT p.name, p.category, p.brand, "
        f"SUM(s.total) as revenue, SUM(s.gross_profit) as gross_profit, "
        f"AVG(s.margin_pct) as avg_margin, SUM(s.quantity) as units "
        f"FROM fact_sales s JOIN dim_products p ON s.product_id = p.product_id "
        f"{where} GROUP BY s.product_id ORDER BY {order_col} DESC LIMIT :n",
        params
    )


def bottom_products(n: int = 10, period: str | None = None) -> pd.DataFrame:
    """Bottom N products by revenue — candidates to discontinue."""
    where = "WHERE s.status='posted'"
    params: dict = {"n": n}
    if period:
        where += " AND s.date_id LIKE :p"
        params["p"] = f"{period}%"

    return query_df(
        f"SELECT p.name, p.category, p.brand, "
        f"SUM(s.total) as revenue, AVG(s.margin_pct) as avg_margin, "
        f"SUM(s.quantity) as units "
        f"FROM fact_sales s JOIN dim_products p ON s.product_id = p.product_id "
        f"{where} GROUP BY s.product_id ORDER BY revenue ASC LIMIT :n",
        params
    )


def top_customers(n: int = 10, period: str | None = None) -> pd.DataFrame:
    """Top N customers by revenue."""
    where = "WHERE s.status='posted'"
    params: dict = {"n": n}
    if period:
        where += " AND s.date_id LIKE :p"
        params["p"] = f"{period}%"

    return query_df(
        f"SELECT c.name, c.segment, c.city, "
        f"SUM(s.total) as revenue, SUM(s.gross_profit) as gross_profit, "
        f"AVG(s.margin_pct) as avg_margin, "
        f"COUNT(DISTINCT s.invoice_number) as n_invoices "
        f"FROM fact_sales s JOIN dim_customers c ON s.customer_id = c.customer_id "
        f"{where} GROUP BY s.customer_id ORDER BY revenue DESC LIMIT :n",
        params
    )


def seller_performance(period: str | None = None) -> pd.DataFrame:
    """Seller performance vs targets."""
    where = "WHERE s.status='posted'"
    params = {}
    if period:
        where += " AND s.date_id LIKE :p"
        params["p"] = f"{period}%"

    return query_df(
        f"SELECT sl.name, sl.team, sl.target_monthly, "
        f"SUM(s.total) as revenue, SUM(s.gross_profit) as gross_profit, "
        f"COUNT(DISTINCT s.invoice_number) as n_invoices, "
        f"COUNT(DISTINCT s.customer_id) as n_customers "
        f"FROM fact_sales s JOIN dim_sellers sl ON s.seller_id = sl.seller_id "
        f"{where} GROUP BY s.seller_id ORDER BY revenue DESC",
        params
    )


def rfm_analysis() -> pd.DataFrame:
    """RFM (Recency, Frequency, Monetary) customer segmentation."""
    today = date.today().isoformat()
    df = query_df(
        "SELECT s.customer_id, c.name, c.segment, "
        "MAX(s.date_id) as last_purchase, "
        "COUNT(DISTINCT s.invoice_number) as frequency, "
        "SUM(s.total) as monetary "
        "FROM fact_sales s JOIN dim_customers c ON s.customer_id = c.customer_id "
        "WHERE s.status='posted' "
        "GROUP BY s.customer_id"
    )
    if df.empty:
        return df

    # Recency: days since last purchase
    df["recency_days"] = (pd.to_datetime(today) - pd.to_datetime(df["last_purchase"])).dt.days

    # Score 1-5 (5 = best)
    for col, ascending in [("recency_days", True), ("frequency", False), ("monetary", False)]:
        df[f"{col}_score"] = pd.qcut(df[col], q=5, labels=[5, 4, 3, 2, 1] if ascending else [1, 2, 3, 4, 5], duplicates="drop").astype(int)

    df["rfm_score"] = df["recency_days_score"] + df["frequency_score"] + df["monetary_score"]

    # Segment labels
    def label(score: int) -> str:
        if score >= 12:
            return "Champions"
        elif score >= 9:
            return "Loyal"
        elif score >= 6:
            return "At Risk"
        else:
            return "Lost"

    df["rfm_segment"] = df["rfm_score"].apply(label)
    return df.sort_values("rfm_score", ascending=False)


def revenue_vs_margin_scatter(period: str | None = None) -> pd.DataFrame:
    """Revenue vs margin per product — for scatter plot."""
    where = "WHERE s.status='posted'"
    params = {}
    if period:
        where += " AND s.date_id LIKE :p"
        params["p"] = f"{period}%"

    return query_df(
        f"SELECT p.name, p.category, "
        f"SUM(s.total) as revenue, AVG(s.margin_pct) as avg_margin "
        f"FROM fact_sales s JOIN dim_products p ON s.product_id = p.product_id "
        f"{where} GROUP BY s.product_id",
        params
    )
