"""Prompt templates for inventory analysis."""

INVENTORY_ANALYSIS = """Analiza el inventario actual.

DATOS:
{data}

Genera:
1. **SALUD DEL INVENTARIO** — score general + justificación.
2. **ACCIONES INMEDIATAS** — qué comprar hoy, qué liquidar.
3. **CAPITAL ATRAPADO** — cuánto dinero está en productos de baja rotación.
4. **RECOMENDACIÓN DE PEDIDO** — basada en datos, no genérica.
5. **ALERTA DE STOCKOUT** — qué productos se van a agotar y cuándo.
6. **ESTACIONALIDAD** detectada si aplica.

Sé directo, usa números específicos."""
