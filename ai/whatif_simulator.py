"""What-If scenario simulator — calculates impact on P&L, cash flow, and ratios."""

import json
from typing import Any

from loguru import logger

from analytics.kpi_calculator import financial_kpis, cashflow_kpis, sales_kpis
from ai.cache_manager import get_cached, set_cache


def simulate_scenario(scenario: dict, period: str | None = None) -> dict:
    """Simulate a what-if scenario and return projected impact.

    Args:
        scenario: Dict with keys like:
            - sales_change_pct: % change in sales (e.g., -15 for -15%)
            - cost_change_pct: % change in COGS
            - opex_change_pct: % change in operating expenses
            - dso_change_days: change in DSO (e.g., +10 means 10 more days)
            - new_investment: one-time cash outflow
            - fixed_expense_change: monthly change in fixed expenses
        period: Reference period for baseline

    Returns:
        Dict with baseline, projected, and delta for P&L, cash flow, ratios.
    """
    fx = financial_kpis(period)
    cx = cashflow_kpis()
    sx = sales_kpis(period)

    # Baseline values
    base_revenue = fx["revenue"]
    base_cogs = fx["cogs"]
    base_opex = base_revenue - fx["gross_profit"] - fx["net_income"]  # approximate
    base_cash = cx["current_balance"]
    base_dso = 34.5  # from receivables

    # Apply scenario adjustments
    sales_pct = scenario.get("sales_change_pct", 0) / 100
    cost_pct = scenario.get("cost_change_pct", 0) / 100
    opex_pct = scenario.get("opex_change_pct", 0) / 100
    dso_delta = scenario.get("dso_change_days", 0)
    investment = scenario.get("new_investment", 0)
    fixed_delta = scenario.get("fixed_expense_change", 0)

    # Projected P&L
    proj_revenue = base_revenue * (1 + sales_pct)
    proj_cogs = base_cogs * (1 + cost_pct) * (1 + sales_pct)  # COGS scales with sales
    proj_gross = proj_revenue - proj_cogs
    proj_opex = (base_revenue * (1 - fx["gross_margin_pct"]/100) - fx["cogs"]) * (1 + opex_pct) + fixed_delta
    # Simplified: use actual opex from financials
    actual_opex = fx["revenue"] - fx["gross_profit"] - fx["net_income"] + fx.get("net_income", 0)
    proj_opex = (fx["ebit"] - fx["gross_profit"]) * -1 * (1 + opex_pct) + fixed_delta
    proj_ebit = proj_gross - abs(proj_opex)
    proj_net = proj_ebit * 0.75  # Approximate 25% tax

    proj_gross_margin = proj_gross / proj_revenue * 100 if proj_revenue else 0
    proj_net_margin = proj_net / proj_revenue * 100 if proj_revenue else 0

    # Cash flow impact
    # DSO change affects cash: more DSO = more cash tied up in receivables
    daily_sales = proj_revenue / 30
    cash_tied_dso = daily_sales * dso_delta  # Additional cash locked in CxC
    monthly_net_change = (proj_revenue - base_revenue) - (proj_cogs - base_cogs) - fixed_delta
    proj_cash_30d = base_cash + monthly_net_change - cash_tied_dso - investment
    proj_cash_60d = proj_cash_30d + monthly_net_change - cash_tied_dso * 0.5
    proj_cash_90d = proj_cash_60d + monthly_net_change

    # Projected ratios
    proj_current_ratio = fx["current_ratio"] * (1 + sales_pct * 0.3)  # Simplified
    proj_roe = proj_net / fx["equity"] * 100 if fx["equity"] else 0

    return {
        "scenario": scenario,
        "baseline": {
            "revenue": round(base_revenue, 2),
            "gross_profit": round(fx["gross_profit"], 2),
            "gross_margin_pct": round(fx["gross_margin_pct"], 1),
            "net_income": round(fx["net_income"], 2),
            "net_margin_pct": round(fx["net_margin_pct"], 1),
            "cash_balance": round(base_cash, 2),
            "current_ratio": fx["current_ratio"],
            "roe": round(fx["roe"], 1),
        },
        "projected": {
            "revenue": round(proj_revenue, 2),
            "gross_profit": round(proj_gross, 2),
            "gross_margin_pct": round(proj_gross_margin, 1),
            "net_income": round(proj_net, 2),
            "net_margin_pct": round(proj_net_margin, 1),
            "cash_30d": round(proj_cash_30d, 2),
            "cash_60d": round(proj_cash_60d, 2),
            "cash_90d": round(proj_cash_90d, 2),
            "current_ratio": round(proj_current_ratio, 2),
            "roe": round(proj_roe, 1),
        },
        "delta": {
            "revenue": round(proj_revenue - base_revenue, 2),
            "revenue_pct": round(sales_pct * 100, 1),
            "gross_profit": round(proj_gross - fx["gross_profit"], 2),
            "net_income": round(proj_net - fx["net_income"], 2),
            "cash_impact_30d": round(proj_cash_30d - base_cash, 2),
            "cash_impact_90d": round(proj_cash_90d - base_cash, 2),
        },
    }


def ai_scenario_analysis(engine: Any, scenario: dict, results: dict) -> str:
    """Get AI interpretation of a what-if scenario.

    Args:
        engine: AIEngine instance
        scenario: The scenario parameters
        results: Output from simulate_scenario()
    """
    cache_data = {"scenario": scenario, "results": results}
    cached = get_cached("whatif", "scenario", cache_data)
    if cached:
        return cached

    prompt = (
        "El CEO quiere simular el siguiente escenario:\n\n"
        f"**Parámetros:**\n{json.dumps(scenario, ensure_ascii=False, indent=2)}\n\n"
        f"**Resultados calculados:**\n{json.dumps(results, default=str, ensure_ascii=False, indent=2)}\n\n"
        "Genera un análisis ejecutivo:\n"
        "1. **IMPACTO EN P&L** — cómo cambia la rentabilidad\n"
        "2. **IMPACTO EN CAJA** — proyección a 30/60/90 días\n"
        "3. **NIVEL DE RIESGO** — bajo/medio/alto con justificación\n"
        "4. **RECOMENDACIÓN** — ¿debería proceder? ¿qué mitigar?\n"
        "5. **ALTERNATIVAS** — qué más podría hacer para lograr el mismo objetivo\n\n"
        "Sé directo, usa números específicos."
    )

    text, tokens = engine.call_claude(prompt)
    set_cache("whatif", "scenario", cache_data, prompt, text, tokens)
    return text
