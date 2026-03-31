"""Prompt templates for accounts payable analysis."""

PAYABLES_ANALYSIS = """Analiza cuentas por pagar.

DATOS:
{data}

Genera:
1. **DIAGNÓSTICO DE LIQUIDEZ** — ¿podemos cubrir las obligaciones?
2. **PLAN DE PAGOS PRIORIZADO** — qué pagar primero y por qué.
3. **RIESGOS** — proveedores que pueden cortar suministro.
4. **OPORTUNIDADES** — descuentos por pronto pago, renegociación.
5. **PROYECCIÓN** — necesidad de financiamiento si hay gap de liquidez.

Sé directo, usa números específicos."""
