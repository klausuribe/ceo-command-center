"""Forecasting — moving average baseline + AI adjustment."""

import json
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from database.db_manager import query_df, query_scalar
from ai.cache_manager import get_cached, set_cache


def _moving_average_forecast(
    series: pd.Series, periods_ahead: int = 3, window: int = 6
) -> list[dict]:
    """Simple moving average forecast with trend adjustment."""
    if len(series) < window:
        window = max(2, len(series))

    ma = series.rolling(window=window).mean()
    last_ma = ma.iloc[-1]

    # Detect trend from last 6 points
    if len(series) >= 6:
        recent = series.tail(6)
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent.values, 1)[0]
    else:
        slope = 0

    forecasts = []
    for i in range(1, periods_ahead + 1):
        base = last_ma + slope * i
        forecasts.append({
            "period_offset": i,
            "base": round(float(base), 2),
            "optimistic": round(float(base * 1.10), 2),
            "pessimistic": round(float(base * 0.90), 2),
            "confidence": max(50, round(90 - i * 10, 0)),  # Decreases over time
        })

    return forecasts


def forecast_sales(periods_ahead: int = 3) -> dict:
    """Forecast monthly sales revenue."""
    df = query_df(
        "SELECT substr(date_id,1,7) as period, SUM(total) as revenue "
        "FROM fact_sales WHERE status='posted' "
        "GROUP BY period ORDER BY period"
    )
    if df.empty:
        return {"forecasts": [], "historical": []}

    forecasts = _moving_average_forecast(df["revenue"], periods_ahead)

    return {
        "historical": df.tail(12).to_dict("records"),
        "forecasts": forecasts,
        "trend": "upward" if forecasts[0]["base"] > df["revenue"].tail(3).mean() else "downward",
    }


def forecast_cashflow(periods_ahead: int = 3) -> dict:
    """Forecast monthly net cash flow."""
    df = query_df(
        "SELECT substr(date_id,1,7) as period, SUM(net_flow) as net_flow "
        "FROM fact_cashflow WHERE is_projected = 0 "
        "GROUP BY period ORDER BY period"
    )
    if df.empty:
        return {"forecasts": [], "historical": []}

    forecasts = _moving_average_forecast(df["net_flow"], periods_ahead)

    current_balance = query_scalar(
        "SELECT running_balance FROM fact_cashflow "
        "WHERE is_projected = 0 ORDER BY date_id DESC, cashflow_id DESC LIMIT 1"
    ) or 0

    # Project balances
    balance = current_balance
    for f in forecasts:
        balance += f["base"]
        f["projected_balance"] = round(balance, 2)

    return {
        "historical": df.tail(12).to_dict("records"),
        "forecasts": forecasts,
        "current_balance": current_balance,
    }


def forecast_expenses(periods_ahead: int = 3) -> dict:
    """Forecast monthly expenses."""
    df = query_df(
        "SELECT substr(date_id,1,7) as period, SUM(amount) as expenses "
        "FROM fact_expenses GROUP BY period ORDER BY period"
    )
    if df.empty:
        return {"forecasts": [], "historical": []}

    forecasts = _moving_average_forecast(df["expenses"], periods_ahead)

    return {
        "historical": df.tail(12).to_dict("records"),
        "forecasts": forecasts,
    }


def ai_adjusted_forecast(engine: Any, module: str = "sales") -> str:
    """Get AI-adjusted forecast with context and assumptions.

    Args:
        engine: AIEngine instance
        module: Module to forecast (sales, cashflow, expenses)
    """
    forecast_fn = {
        "sales": forecast_sales,
        "cashflow": forecast_cashflow,
        "expenses": forecast_expenses,
    }

    if module not in forecast_fn:
        return f"Módulo '{module}' no soporta forecasting."

    forecast_data = forecast_fn[module]()

    # Get active assumptions
    from database.db_manager import query_df as qdf
    assumptions = qdf(
        "SELECT description, impact_type, impact_value, impact_pct "
        "FROM config_assumptions WHERE is_active = 1 AND module = :m",
        {"m": module}
    ).to_dict("records")

    cache_data = {"forecast": forecast_data, "assumptions": assumptions}
    cached = get_cached(module, "forecast", cache_data)
    if cached:
        return cached

    prompt = (
        f"Forecast estadístico baseline para {module}:\n"
        f"{json.dumps(forecast_data, default=str, ensure_ascii=False, indent=2)}\n\n"
        f"Supuestos del usuario: {json.dumps(assumptions, default=str, ensure_ascii=False)}\n\n"
        "Ajusta el forecast considerando:\n"
        "1. Los supuestos manuales del usuario\n"
        "2. Estacionalidad que detectes en los datos históricos\n"
        "3. Tendencias recientes\n\n"
        "Genera:\n"
        "- Forecast ajustado (optimista / base / pesimista) con números\n"
        "- Nivel de confianza (%)\n"
        "- Supuestos clave utilizados\n"
        "- Riesgos principales del forecast\n\n"
        "Sé directo, usa números específicos."
    )

    text, tokens = engine.call_claude(prompt)
    set_cache(module, "forecast", cache_data, prompt, text, tokens)
    return text
