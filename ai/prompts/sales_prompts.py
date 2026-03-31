"""Prompt templates for sales analysis."""

SALES_ANALYSIS = """Analiza los datos de ventas del periodo {period}.

DATOS:
{data}

Genera:
1. **DIAGNÓSTICO** — qué pasó y por qué (máx 150 palabras). Usa números específicos.
2. **ANOMALÍAS** — cambios inusuales en patrones de venta.
3. **OPORTUNIDADES** — productos/clientes con potencial sub-explotado.
4. **RIESGOS** — concentración, dependencia, márgenes comprimidos.
5. **RECOMENDACIONES ACCIONABLES** — 3-5 acciones concretas con impacto estimado.

Sé directo, usa números específicos. No seas genérico."""

SELLER_ANALYSIS = """Analiza el desempeño de los vendedores para el periodo {period}.

DATOS:
{data}

Genera:
1. **RANKING** — quién cumple y quién no, con % de cumplimiento.
2. **PATRONES** — diferencias en mix de clientes o productos entre vendedores.
3. **ACCIONES** — recomendaciones específicas para mejorar cada vendedor.

Sé directo, usa números específicos."""

CUSTOMER_ANALYSIS = """Analiza la segmentación de clientes basada en RFM.

DATOS:
{data}

Genera:
1. **CHAMPIONS** — quiénes son y cómo retenerlos.
2. **AT RISK** — clientes valiosos que están bajando actividad.
3. **LOST** — vale la pena recuperarlos? Cuáles?
4. **ACCIONES** — estrategia por segmento (máx 3 bullets por segmento).

Sé directo, usa números específicos."""
