"""Prompt templates for accounts receivable analysis."""

RECEIVABLES_ANALYSIS = """Analiza la cartera de cuentas por cobrar.

DATOS:
{data}

Genera:
1. **ESTADO DE LA CARTERA** — salud general (semáforo: verde/amarillo/rojo) con justificación.
2. **CLIENTES CRÍTICOS** — quiénes necesitan acción inmediata y por qué.
3. **RIESGO DE INCOBRABILIDAD** — estimación basada en aging y comportamiento.
4. **PLAN DE COBRANZA PRIORIZADO** — orden de acción con montos.
5. **IMPACTO EN FLUJO DE CAJA** — proyección realista de cobros a 30 días.

Sé directo, usa números específicos."""
