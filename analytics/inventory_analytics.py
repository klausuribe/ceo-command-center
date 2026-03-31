"""Inventory analytics — ABC classification, rotation, stockout risk, reorder."""

import pandas as pd
from database.db_manager import query_df


def abc_classification() -> pd.DataFrame:
    """ABC classification by inventory value (Pareto)."""
    df = query_df(
        "SELECT i.product_id, p.name, p.category, p.product_line, "
        "i.total_value, i.qty_on_hand, i.avg_daily_sales, "
        "i.days_of_stock, i.rotation_class "
        "FROM fact_inventory i "
        "JOIN dim_products p ON i.product_id = p.product_id "
        "ORDER BY i.total_value DESC"
    )
    if df.empty:
        return df
    total = df["total_value"].sum()
    df["value_pct"] = df["total_value"] / total * 100
    df["cumulative_pct"] = df["value_pct"].cumsum()
    df["abc_value"] = df["cumulative_pct"].apply(
        lambda x: "A" if x <= 80 else ("B" if x <= 95 else "C")
    )
    return df


def rotation_analysis() -> pd.DataFrame:
    """Rotation quadrant analysis: value vs days of stock."""
    return query_df(
        "SELECT i.product_id, p.name, p.category, "
        "i.total_value, i.days_of_stock, i.avg_daily_sales, "
        "i.rotation_class, i.qty_on_hand "
        "FROM fact_inventory i "
        "JOIN dim_products p ON i.product_id = p.product_id "
        "ORDER BY i.total_value DESC"
    )


def critical_levels() -> dict:
    """Products at critical inventory levels."""
    below_reorder = query_df(
        "SELECT p.name, p.category, i.qty_available, i.reorder_point, "
        "i.days_of_stock, i.avg_daily_sales "
        "FROM fact_inventory i "
        "JOIN dim_products p ON i.product_id = p.product_id "
        "WHERE i.qty_available <= i.reorder_point AND i.rotation_class IN ('A','B') "
        "ORDER BY i.days_of_stock"
    )

    zero_stock = query_df(
        "SELECT p.name, p.category, i.avg_daily_sales "
        "FROM fact_inventory i "
        "JOIN dim_products p ON i.product_id = p.product_id "
        "WHERE i.qty_on_hand = 0 AND i.avg_daily_sales > 0"
    )

    overstock = query_df(
        "SELECT p.name, p.category, i.qty_on_hand, i.total_value, "
        "i.days_of_stock "
        "FROM fact_inventory i "
        "JOIN dim_products p ON i.product_id = p.product_id "
        "WHERE i.days_of_stock > 90 AND i.rotation_class != 'dead_stock' "
        "ORDER BY i.total_value DESC"
    )

    dead_stock = query_df(
        "SELECT p.name, p.category, i.qty_on_hand, i.total_value, "
        "i.days_since_last_sale "
        "FROM fact_inventory i "
        "JOIN dim_products p ON i.product_id = p.product_id "
        "WHERE i.rotation_class = 'dead_stock' "
        "ORDER BY i.total_value DESC"
    )

    return {
        "below_reorder": below_reorder,
        "zero_stock": zero_stock,
        "overstock": overstock,
        "dead_stock": dead_stock,
    }


def reorder_suggestions() -> pd.DataFrame:
    """Suggested reorder quantities based on sales velocity and lead time."""
    return query_df(
        "SELECT p.name, p.category, v.name as vendor, "
        "i.qty_available, i.reorder_point, i.reorder_qty, "
        "i.avg_daily_sales, i.days_of_stock, "
        "CASE "
        "  WHEN i.qty_available <= 0 THEN 'URGENTE' "
        "  WHEN i.days_of_stock < 7 THEN 'Alta' "
        "  WHEN i.days_of_stock < 15 THEN 'Media' "
        "  ELSE 'Baja' "
        "END as urgency "
        "FROM fact_inventory i "
        "JOIN dim_products p ON i.product_id = p.product_id "
        "LEFT JOIN dim_vendors v ON v.vendor_id = ("
        "  SELECT vendor_id FROM fact_payables "
        "  WHERE vendor_id IS NOT NULL LIMIT 1"
        ") "
        "WHERE i.qty_available <= i.reorder_point "
        "ORDER BY i.days_of_stock"
    )


def inventory_value_by_category() -> pd.DataFrame:
    """Inventory value distribution by product category."""
    return query_df(
        "SELECT p.category, "
        "COUNT(*) as n_products, "
        "SUM(i.total_value) as total_value, "
        "AVG(i.days_of_stock) as avg_days_stock, "
        "SUM(CASE WHEN i.rotation_class='A' THEN 1 ELSE 0 END) as class_a, "
        "SUM(CASE WHEN i.rotation_class='dead_stock' THEN 1 ELSE 0 END) as dead "
        "FROM fact_inventory i "
        "JOIN dim_products p ON i.product_id = p.product_id "
        "GROUP BY p.category ORDER BY total_value DESC"
    )
