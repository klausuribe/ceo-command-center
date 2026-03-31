"""Anomaly detection — statistical (Z-score/IQR) + AI interpretation."""

import json
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from config.ai_config import Z_SCORE_THRESHOLD, IQR_MULTIPLIER
from database.db_manager import query_df
from ai.cache_manager import get_cached, set_cache


def _zscore_detect(series: pd.Series, threshold: float = Z_SCORE_THRESHOLD) -> pd.Series:
    """Return boolean mask of values beyond threshold standard deviations."""
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(False, index=series.index)
    z = (series - mean).abs() / std
    return z > threshold


def _iqr_detect(series: pd.Series, multiplier: float = IQR_MULTIPLIER) -> pd.Series:
    """Return boolean mask using IQR method."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    return (series < lower) | (series > upper)


def detect_sales_anomalies() -> list[dict]:
    """Detect anomalies in daily sales revenue."""
    df = query_df(
        "SELECT date_id, SUM(total) as revenue, SUM(gross_profit) as profit, "
        "COUNT(DISTINCT invoice_number) as n_invoices "
        "FROM fact_sales WHERE status='posted' "
        "GROUP BY date_id ORDER BY date_id"
    )
    if len(df) < 30:
        return []

    anomalies = []
    for col in ["revenue", "profit", "n_invoices"]:
        mask = _zscore_detect(df[col]) | _iqr_detect(df[col])
        for _, row in df[mask].iterrows():
            mean_val = df[col].mean()
            anomalies.append({
                "date": row["date_id"],
                "metric": col,
                "value": round(float(row[col]), 2),
                "mean": round(float(mean_val), 2),
                "deviation_pct": round((float(row[col]) - mean_val) / mean_val * 100, 1),
                "direction": "above" if row[col] > mean_val else "below",
            })
    return anomalies


def detect_expense_anomalies() -> list[dict]:
    """Detect anomalies in monthly expenses by account."""
    df = query_df(
        "SELECT account_id, substr(date_id,1,7) as period, SUM(amount) as amount "
        "FROM fact_expenses GROUP BY account_id, period"
    )
    if df.empty:
        return []

    anomalies = []
    for acc_id, group in df.groupby("account_id"):
        if len(group) < 6:
            continue
        mask = _zscore_detect(group["amount"])
        for _, row in group[mask].iterrows():
            mean_val = group["amount"].mean()
            anomalies.append({
                "account_id": int(acc_id),
                "period": row["period"],
                "amount": round(float(row["amount"]), 2),
                "mean": round(float(mean_val), 2),
                "deviation_pct": round((float(row["amount"]) - mean_val) / mean_val * 100, 1),
            })
    return anomalies


def detect_receivables_anomalies() -> list[dict]:
    """Detect anomalies in receivables — unusual balances or aging."""
    df = query_df(
        "SELECT r.customer_id, c.name, SUM(r.balance) as balance, "
        "AVG(r.days_overdue) as avg_overdue, COUNT(*) as n_invoices "
        "FROM fact_receivables r "
        "JOIN dim_customers c ON r.customer_id = c.customer_id "
        "WHERE r.status != 'paid' "
        "GROUP BY r.customer_id"
    )
    if len(df) < 5:
        return []

    anomalies = []
    for col in ["balance", "avg_overdue"]:
        mask = _zscore_detect(df[col])
        for _, row in df[mask].iterrows():
            anomalies.append({
                "customer": row["name"],
                "metric": col,
                "value": round(float(row[col]), 2),
                "mean": round(float(df[col].mean()), 2),
            })
    return anomalies


def detect_all() -> dict[str, list[dict]]:
    """Run all anomaly detectors."""
    return {
        "sales": detect_sales_anomalies(),
        "expenses": detect_expense_anomalies(),
        "receivables": detect_receivables_anomalies(),
    }


def interpret_anomalies(engine: Any, anomalies: dict[str, list]) -> str:
    """Send detected anomalies to Claude for interpretation.

    Args:
        engine: AIEngine instance
        anomalies: Output from detect_all()
    """
    # Filter out empty modules
    non_empty = {k: v for k, v in anomalies.items() if v}
    if not non_empty:
        return "No se detectaron anomalías significativas en los datos actuales."

    cached = get_cached("anomalies", "interpretation", non_empty)
    if cached:
        return cached

    prompt = (
        "Se detectaron las siguientes anomalías estadísticas en los datos del negocio:\n\n"
        f"{json.dumps(non_empty, default=str, ensure_ascii=False, indent=2)}\n\n"
        "Para cada anomalía:\n"
        "1. ¿Es realmente preocupante o tiene explicación normal (estacionalidad, etc.)?\n"
        "2. Nivel de severidad: 🔴 Crítico / 🟡 Atención / 🟢 Informativo\n"
        "3. Acción recomendada\n\n"
        "Sé directo, usa números específicos."
    )

    text, tokens = engine.call_claude(prompt)
    set_cache("anomalies", "interpretation", non_empty, prompt, text, tokens)
    return text
