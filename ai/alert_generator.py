"""Cross-module intelligent alert generation."""

import json
from typing import Any

from loguru import logger

from analytics.kpi_calculator import (
    sales_kpis, receivables_kpis, payables_kpis,
    inventory_kpis, expense_kpis, cashflow_kpis,
)
from ai.cache_manager import get_cached, set_cache
from config.ai_config import ALERT_THRESHOLDS
from config.settings import DEFAULT_CURRENCY


def _rule_based_alerts() -> list[dict]:
    """Generate alerts from hardcoded business rules (no AI needed)."""
    alerts = []

    t = ALERT_THRESHOLDS

    # Receivables
    rx = receivables_kpis()
    if rx["over_90"] > 0:
        alerts.append({
            "level": "critical",
            "module": "receivables",
            "title": "CxC vencidas >90 días",
            "description": f"{DEFAULT_CURRENCY} {rx['over_90']:,.0f} en facturas vencidas más de 90 días.",
            "action": "Revisar clientes con facturas >90 días y escalar cobranza.",
        })
    if rx["dso"] > t["dso_warning_days"]:
        alerts.append({
            "level": "warning",
            "module": "receivables",
            "title": f"DSO alto: {rx['dso']:.0f} días",
            "description": "El tiempo promedio de cobro supera los 60 días.",
            "action": "Endurecer políticas de crédito y acelerar cobranza.",
        })
    if rx["top5_concentration_pct"] > t["concentration_pct"]:
        alerts.append({
            "level": "warning",
            "module": "receivables",
            "title": f"Concentración CxC: {rx['top5_concentration_pct']:.0f}% en top 5",
            "description": "Alta concentración de riesgo crediticio.",
            "action": "Diversificar cartera de clientes.",
        })

    # Payables
    px = payables_kpis()
    if px["critical_count"] > 0:
        alerts.append({
            "level": "critical",
            "module": "payables",
            "title": f"{int(px['critical_count'])} pagos críticos pendientes",
            "description": f"{DEFAULT_CURRENCY} {px['critical_amount']:,.0f} en pagos con prioridad crítica.",
            "action": "Programar pagos inmediatos a proveedores críticos.",
        })
    if px["due_next_7d"] > 0:
        alerts.append({
            "level": "warning",
            "module": "payables",
            "title": f"CxP próximas: {DEFAULT_CURRENCY} {px['due_next_7d']:,.0f} en 7 días",
            "description": "Pagos programados para la próxima semana.",
            "action": "Verificar disponibilidad de fondos.",
        })

    # Inventory
    ix = inventory_kpis()
    if ix["stockout_risk"] > 0:
        alerts.append({
            "level": "critical",
            "module": "inventory",
            "title": f"{ix['stockout_risk']} productos en riesgo de stockout",
            "description": "Productos A/B con menos de 7 días de stock.",
            "action": "Emitir órdenes de compra urgentes.",
        })
    if ix["dead_stock_value"] > 0:
        alerts.append({
            "level": "info",
            "module": "inventory",
            "title": f"Dead stock: {DEFAULT_CURRENCY} {ix['dead_stock_value']:,.0f}",
            "description": f"{int(ix['dead_stock_count'])} productos sin movimiento.",
            "action": "Evaluar liquidación o descontinuación.",
        })

    # Expenses
    ex = expense_kpis()
    if ex["variance_pct"] > t["expense_variance_over_pct"]:
        alerts.append({
            "level": "warning",
            "module": "expenses",
            "title": f"Gastos {ex['variance_pct']:+.1f}% sobre presupuesto",
            "description": f"Desviación de {DEFAULT_CURRENCY} {ex['total_variance']:,.0f} vs presupuesto.",
            "action": "Revisar partidas con mayor desviación.",
        })
    elif ex["variance_pct"] < t["expense_variance_under_pct"]:
        alerts.append({
            "level": "positive",
            "module": "expenses",
            "title": f"Gastos {abs(ex['variance_pct']):.1f}% bajo presupuesto",
            "description": "Buen control de gastos este periodo.",
            "action": "Mantener disciplina presupuestaria.",
        })

    # Sales
    sx = sales_kpis()
    if sx["mom_change_pct"] > t["mom_change_pct"]:
        alerts.append({
            "level": "positive",
            "module": "sales",
            "title": f"Ventas +{sx['mom_change_pct']:.0f}% vs mes anterior",
            "description": f"Revenue: {DEFAULT_CURRENCY} {sx['revenue']:,.0f}",
            "action": "Analizar qué impulsó el crecimiento para replicar.",
        })
    elif sx["mom_change_pct"] < -t["mom_change_pct"]:
        alerts.append({
            "level": "warning",
            "module": "sales",
            "title": f"Ventas {sx['mom_change_pct']:.0f}% vs mes anterior",
            "description": "Caída significativa en ventas.",
            "action": "Investigar causas y activar plan comercial.",
        })

    # Cashflow
    cx = cashflow_kpis()
    if cx["runway_days"] is not None and cx["runway_days"] < t["cash_runway_critical_days"]:
        alerts.append({
            "level": "critical",
            "module": "cashflow",
            "title": f"Runway: {int(cx['runway_days'])} días de caja",
            "description": "Al ritmo actual, el efectivo se agota pronto.",
            "action": "Acelerar cobros y postergar pagos no urgentes.",
        })

    # Sort: critical first, then warning, info, positive
    order = {"critical": 0, "warning": 1, "info": 2, "positive": 3}
    alerts.sort(key=lambda a: order.get(a["level"], 9))

    return alerts


def generate_alerts() -> list[dict]:
    """Generate all business alerts (rule-based)."""
    return _rule_based_alerts()


def ai_enhanced_alerts(engine: Any) -> str:
    """Generate AI-enhanced cross-module alerts.

    Uses rule-based alerts as input, then asks Claude for deeper analysis.
    """
    alerts = _rule_based_alerts()
    if not alerts:
        return "No hay alertas activas. Todo parece estar en orden."

    summary = {
        "alerts": alerts,
        "sales": sales_kpis(),
        "cashflow": cashflow_kpis(),
    }

    cached = get_cached("alerts", "ai_enhanced", summary)
    if cached:
        return cached

    prompt = (
        "Estas son las alertas de negocio detectadas automáticamente:\n\n"
        f"{json.dumps(alerts, default=str, ensure_ascii=False, indent=2)}\n\n"
        "Contexto adicional:\n"
        f"Ventas del mes: {DEFAULT_CURRENCY} {summary['sales']['revenue']:,.0f}\n"
        f"Cash actual: {DEFAULT_CURRENCY} {summary['cashflow']['current_balance']:,.0f}\n\n"
        "Genera un análisis ejecutivo de 200 palabras:\n"
        "1. ¿Cuáles son las 3 alertas MÁS importantes y por qué?\n"
        "2. ¿Hay conexiones entre las alertas (efecto dominó)?\n"
        "3. ¿Cuál es la PRIMERA acción que debe tomar el CEO hoy?\n\n"
        "Sé directo, usa números específicos."
    )

    text, tokens = engine.call_claude(prompt)
    set_cache("alerts", "ai_enhanced", summary, prompt, text, tokens)
    return text
