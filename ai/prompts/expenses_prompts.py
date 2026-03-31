"""Prompt templates for expense analysis."""

EXPENSE_ANALYSIS = """Analiza gastos del periodo {period}.

DATOS:
{data}

Genera:
1. **DIAGNÓSTICO** — ¿estamos dentro del presupuesto? ¿por qué?
2. **DESVIACIONES IMPORTANTES** — cuáles y posibles causas.
3. **GASTOS INUSUALES** — cualquier anomalía detectada.
4. **TENDENCIA** — ¿estamos gastando más o menos con el tiempo?
5. **RECOMENDACIONES DE OPTIMIZACIÓN** — áreas donde reducir sin impacto operativo.

Sé directo, usa números específicos."""
