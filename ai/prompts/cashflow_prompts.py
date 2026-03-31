"""Prompt templates for cash flow analysis."""

CASHFLOW_ANALYSIS = """Analiza el flujo de caja.

DATOS:
{data}

Genera:
1. **POSICIÓN ACTUAL** — ¿estamos bien de liquidez? ¿por cuánto tiempo?
2. **PROYECCIÓN REALISTA** a 30/60/90 días.
3. **PUNTO CRÍTICO** — ¿cuándo podríamos tener problemas de caja?
4. **ESCENARIOS** — optimista/base/pesimista con números.
5. **RECOMENDACIONES DE TESORERÍA** — acciones para optimizar caja.
6. **ALERTAS** — pagos grandes próximos, gaps de liquidez detectados.

Sé directo, usa números específicos."""
