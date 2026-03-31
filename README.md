# CEO Command Center

**AI-Powered Business Intelligence Platform**

Dashboard ejecutivo que centraliza todas las áreas críticas de negocio en una sola interfaz, potenciado por inteligencia artificial (Claude API) para análisis narrativo, detección de anomalías, proyecciones y chat interactivo.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.55-red)
![Claude AI](https://img.shields.io/badge/AI-Claude%20Sonnet-purple)
![SQLite](https://img.shields.io/badge/DB-SQLite-green)
![License](https://img.shields.io/badge/License-Private-gray)

---

## Módulos

| Módulo | Descripción |
|--------|-------------|
| **Resumen Ejecutivo** | KPIs consolidados, Morning Briefing IA, alertas cross-módulo |
| **Ventas** | Tendencias, Pareto, rankings, sellers vs target, RFM, scatter rentabilidad |
| **Cuentas por Cobrar** | Aging report, DSO, credit scoring, plan de cobranza priorizado |
| **Cuentas por Pagar** | Priorización de pagos, cash vs payables, DPO por proveedor |
| **Inventarios** | Clasificación ABC, rotación, stockout risk, sugerencias de reposición |
| **Gastos** | Presupuesto vs real, centro de costo, detección de anomalías (Z-score) |
| **Estados Financieros** | P&L, Balance, ratios (liquidez, eficiencia, apalancamiento), CCC |
| **Flujo de Caja** | Saldo diario, waterfall, proyección 3 escenarios, breakeven |
| **Chat IA** | Preguntas en lenguaje natural, simulador What-If, gestión de supuestos |

## Stack Tecnológico

- **Frontend:** Streamlit (multi-page app, dark theme)
- **Base de Datos:** SQLite (star schema — 7 dimensiones, 7 hechos, 6 soporte)
- **Motor IA:** Claude API (Anthropic) — análisis, anomalías, forecasting, chat
- **Visualización:** Plotly (line, bar, pie, scatter, treemap, waterfall, gauge)
- **Autenticación:** streamlit-authenticator (bcrypt)
- **Analytics:** Pandas, NumPy, SQLAlchemy

## Quick Start

```bash
# Clonar repositorio
git clone https://github.com/klausuribe/ceo-command-center.git
cd ceo-command-center

# Crear entorno virtual e instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY

# Inicializar base de datos y datos demo
python scripts/init_db.py
python scripts/generate_demo_data.py

# Lanzar la aplicación
streamlit run app/Home.py
```

**Login:** `ceo` / `admin123`

O simplemente:

```bash
bash scripts/run.sh
```

## Configuración

Copia `.env.example` a `.env` y configura:

| Variable | Descripción |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key de Claude (requerida para funciones IA) |
| `ODOO_URL` | URL de instancia Odoo (opcional, para ETL) |
| `ODOO_DB` | Base de datos de Odoo |
| `ODOO_USERNAME` | Usuario de Odoo |
| `ODOO_PASSWORD` | Contraseña de Odoo |
| `DB_PATH` | Ruta de la base de datos SQLite |
| `COMPANY_NAME` | Nombre de la empresa (aparece en el dashboard) |

## Arquitectura

```
ceo-command-center/
├── app/                    # Streamlit UI
│   ├── Home.py             # Entry point — Resumen Ejecutivo
│   ├── components/         # Componentes reutilizables (KPIs, charts, auth)
│   └── pages/              # 8 páginas de módulos
├── analytics/              # Cálculos de KPIs y métricas (sin IA)
├── ai/                     # Motor de IA (Claude API + cache + prompts)
│   ├── engine.py           # Motor central
│   ├── prompts/            # Templates por módulo
│   ├── anomaly_detector.py # Z-score/IQR + interpretación IA
│   ├── alert_generator.py  # Alertas cross-módulo
│   ├── forecaster.py       # Moving average + ajuste IA
│   ├── chat_engine.py      # Chat conversacional
│   └── whatif_simulator.py # Simulador de escenarios
├── database/               # Schema DDL + db_manager (SQLAlchemy)
├── config/                 # Settings, auth, AI config
├── scripts/                # init_db, generate_demo_data, run.sh
└── docs/                   # Especificaciones detalladas
```

**Flujo de datos:**

```
Odoo/Excel → ETL → SQLite → Analytics (Python) → AI (Claude) → Dashboard (Streamlit)
```

## Datos Demo

El generador crea 24 meses de datos sintéticos realistas:

- 164 productos en 5 categorías, 15 líneas, 8 marcas
- 120 clientes en 3 segmentos (A/B/C)
- 25 proveedores
- 5 vendedores con metas
- ~15,000 líneas de venta
- Cuentas por cobrar/pagar con aging realista
- Inventario con clasificación ABC
- Gastos con presupuesto
- Estados financieros mensuales
- Flujo de caja diario

## Funciones de IA

Todas las funciones requieren `ANTHROPIC_API_KEY` configurada:

- **Morning Briefing** — Resumen ejecutivo diario generado por IA
- **Análisis por Módulo** — Diagnóstico, anomalías, oportunidades, recomendaciones
- **Detección de Anomalías** — Estadística (Z-score/IQR) + interpretación IA
- **Alertas Inteligentes** — Cross-módulo con severidad (crítico/warning/info/positivo)
- **Forecasting** — Moving average + ajuste IA con 3 escenarios
- **Chat** — Preguntas en lenguaje natural sobre datos del negocio
- **What-If** — Simulación de escenarios con impacto en P&L y cash flow
- **Cache** — Respuestas cacheadas 4 horas para optimizar costos API

## Autor

**Klaus Uribe** — Marzo 2026
