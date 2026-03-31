"""Prompt templates for financial statement analysis."""

FINANCIAL_ANALYSIS = """Analiza los estados financieros del periodo {period}.

DATOS:
{data}

Genera un ANÁLISIS FINANCIERO EJECUTIVO:
1. **DIAGNÓSTICO GENERAL** — rentabilidad, liquidez, eficiencia (1 párrafo).
2. **FORTALEZAS FINANCIERAS** — qué índices están bien y qué significa.
3. **SEÑALES DE ALERTA** — qué índices se deterioraron y riesgo asociado.
4. **ANÁLISIS DE TENDENCIA** — dirección de los últimos 3-6 meses.
5. **CICLO DE CONVERSIÓN DE EFECTIVO** — análisis del CCC.
6. **RECOMENDACIONES ESTRATÉGICAS** — 3-5 acciones con impacto financiero estimado.

Sé preciso con números. Compara con benchmarks típicos del sector comercial B2B."""
