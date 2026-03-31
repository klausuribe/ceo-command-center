# CEO COMMAND CENTER — AI-Powered Business Intelligence Platform

## Project Plan & Technical Specification v1.0
**Autor:** Klaus Uribe | **Fecha:** Marzo 2026
**Nombre del Proyecto:** CEO Command Center (CCC)
**Stack Principal:** Python + Streamlit + SQLite + Claude API (Anthropic)

---

## 1. VISIÓN GENERAL DEL PROYECTO

### 1.1 ¿Qué es?
Una plataforma web tipo dashboard que centraliza **todas las áreas críticas de negocio** en una sola interfaz, potenciada por **inteligencia artificial (Claude API)** que analiza, detecta anomalías, proyecta y recomienda acciones en tiempo real.

### 1.2 Problema que Resuelve
- Información dispersa entre Odoo, Excel y reportes manuales
- Análisis reactivo en vez de proactivo
- Falta de visión consolidada CEO-level de todas las áreas
- Tiempo excesivo en generar reportes y análisis manuales
- Incapacidad de simular escenarios y proyectar con datos reales

### 1.3 Propuesta de Valor
Un CEO/CFO abre UNA sola app y en menos de 30 segundos tiene:
- Estado actual de cada área del negocio
- Alertas inteligentes de lo que requiere atención
- Análisis narrativo generado por IA (no solo números)
- Proyecciones y recomendaciones accionables
- Chat interactivo para preguntas ad-hoc y simulaciones

---

## 2. ARQUITECTURA GENERAL

### 2.1 Diagrama de Arquitectura (Alto Nivel)

```
┌─────────────────────────────────────────────────────────┐
│                    FUENTES DE DATOS                      │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐   │
│  │  Odoo DB  │  │  Excel/  │  │  Input Manual (Chat) │   │
│  │ (XML-RPC) │  │   CSV    │  │  + Supuestos         │   │
│  └─────┬─────┘  └─────┬────┘  └──────────┬───────────┘   │
│        │              │                   │               │
└────────┼──────────────┼───────────────────┼───────────────┘
         │              │                   │
         ▼              ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│              CAPA ETL (Extract-Transform-Load)           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  odoo_connector.py  │  file_loader.py  │ manual │    │
│  │  - XML-RPC/JSON-RPC │  - pandas read   │ input  │    │
│  │  - Scheduled sync   │  - validation    │ handler│    │
│  │  - Delta updates    │  - cleaning      │        │    │
│  └─────────────────────────────────────────────────┘    │
│                         │                                │
│                         ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │           DATA WAREHOUSE (SQLite)                │    │
│  │  fact_sales │ fact_receivables │ fact_payables   │    │
│  │  fact_inventory │ fact_expenses │ fact_financials│    │
│  │  fact_cashflow │ dim_products │ dim_customers    │    │
│  │  dim_vendors │ dim_accounts │ dim_time           │    │
│  │  config_budgets │ config_targets │ ai_cache      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              CAPA DE INTELIGENCIA (AI ENGINE)             │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Claude API (Anthropic)                │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────┐ │  │
│  │  │  Análisis    │ │  Detección   │ │ Proyección │ │  │
│  │  │  Narrativo   │ │  Anomalías   │ │ & Forecast │ │  │
│  │  └─────────────┘ └──────────────┘ └────────────┘ │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────┐ │  │
│  │  │  What-If     │ │  Alertas     │ │ Chat       │ │  │
│  │  │  Simulator   │ │  Inteligentes│ │ Interactivo│ │  │
│  │  └─────────────┘ └──────────────┘ └────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                CAPA DE PRESENTACIÓN                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Streamlit Web App                     │  │
│  │  ┌─────┐┌──────┐┌─────┐┌──────┐┌─────┐┌───────┐ │  │
│  │  │Home ││Ventas││CxC  ││CxP   ││Inv. ││Gastos │ │  │
│  │  └─────┘└──────┘└─────┘└──────┘└─────┘└───────┘ │  │
│  │  ┌──────────┐┌──────────┐┌────────────────────┐  │  │
│  │  │Financiero││Flujo Caja││ AI Chat + What-If  │  │  │
│  │  └──────────┘└──────────┘└────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Stack Tecnológico Detallado

| Componente | Tecnología | Justificación |
|---|---|---|
| **Frontend/UI** | Streamlit 1.38+ | Velocidad de desarrollo, Python nativo, componentes ricos |
| **Base de Datos** | SQLite (DuckDB como alternativa analítica) | Ligero, sin servidor, perfecto para MVP |
| **Motor IA** | Claude API (claude-sonnet-4-20250514) | Análisis narrativo superior, contexto largo, tool use |
| **ETL/Data** | Python + Pandas + SQLAlchemy | Ecosistema robusto, familiar para Klaus |
| **Conector ERP** | Odoo XML-RPC / JSON-RPC API | Nativo de Odoo, bien documentado |
| **Gráficos** | Plotly + Altair | Interactivos, profesionales, nativos en Streamlit |
| **Scheduling** | APScheduler / Cron | Sincronización automática de datos |
| **Cache IA** | SQLite (tabla ai_cache) | Evitar llamadas repetitivas a la API |
| **Auth** | Streamlit-Authenticator | Control de acceso básico para MVP |

---

## 3. MODELO DE DATOS (DATA WAREHOUSE)

### 3.1 Esquema Star Schema

El diseño sigue un modelo dimensional (star schema) optimizado para análisis.

### 3.2 Tablas de Dimensiones

```sql
-- ============================================
-- DIMENSIONES
-- ============================================

CREATE TABLE dim_time (
    date_id         TEXT PRIMARY KEY,    -- '2026-03-24'
    date            DATE NOT NULL,
    day             INTEGER,
    month           INTEGER,
    month_name      TEXT,
    quarter         INTEGER,
    year            INTEGER,
    week_number     INTEGER,
    day_of_week     INTEGER,
    is_weekend      BOOLEAN,
    fiscal_year     INTEGER,
    fiscal_quarter  INTEGER
);

CREATE TABLE dim_products (
    product_id      INTEGER PRIMARY KEY,
    odoo_product_id INTEGER UNIQUE,
    sku             TEXT,
    name            TEXT NOT NULL,
    category        TEXT,           -- Segmento
    product_line    TEXT,           -- Línea
    brand           TEXT,           -- Marca/Gama
    unit_cost       REAL,
    list_price      REAL,
    margin_pct      REAL,
    is_active       BOOLEAN DEFAULT 1,
    last_updated    TIMESTAMP
);

CREATE TABLE dim_customers (
    customer_id     INTEGER PRIMARY KEY,
    odoo_partner_id INTEGER UNIQUE,
    name            TEXT NOT NULL,
    customer_code   TEXT,
    segment         TEXT,           -- A/B/C classification
    city            TEXT,
    region          TEXT,
    credit_limit    REAL,
    payment_terms   TEXT,
    assigned_seller TEXT,
    is_active       BOOLEAN DEFAULT 1,
    created_date    DATE,
    last_updated    TIMESTAMP
);

CREATE TABLE dim_vendors (
    vendor_id       INTEGER PRIMARY KEY,
    odoo_partner_id INTEGER UNIQUE,
    name            TEXT NOT NULL,
    vendor_code     TEXT,
    category        TEXT,
    country         TEXT,
    currency        TEXT DEFAULT 'BOB',
    payment_terms   TEXT,
    lead_time_days  INTEGER,
    is_active       BOOLEAN DEFAULT 1,
    last_updated    TIMESTAMP
);

CREATE TABLE dim_sellers (
    seller_id       INTEGER PRIMARY KEY,
    odoo_user_id    INTEGER UNIQUE,
    name            TEXT NOT NULL,
    team            TEXT,
    region          TEXT,
    target_monthly  REAL,
    is_active       BOOLEAN DEFAULT 1
);

CREATE TABLE dim_accounts (
    account_id      INTEGER PRIMARY KEY,
    odoo_account_id INTEGER UNIQUE,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    account_type    TEXT,           -- asset/liability/equity/income/expense
    parent_group    TEXT,
    sub_group       TEXT,
    is_active       BOOLEAN DEFAULT 1
);

CREATE TABLE dim_cost_centers (
    cost_center_id  INTEGER PRIMARY KEY,
    code            TEXT,
    name            TEXT NOT NULL,
    department      TEXT,
    responsible     TEXT,
    budget_annual   REAL
);
```

### 3.3 Tablas de Hechos (Facts)

```sql
-- ============================================
-- HECHOS (FACTS)
-- ============================================

-- VENTAS: Granularidad = línea de factura
CREATE TABLE fact_sales (
    sale_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id         TEXT REFERENCES dim_time(date_id),
    invoice_number  TEXT,
    odoo_invoice_id INTEGER,
    product_id      INTEGER REFERENCES dim_products(product_id),
    customer_id     INTEGER REFERENCES dim_customers(customer_id),
    seller_id       INTEGER REFERENCES dim_sellers(seller_id),
    quantity        REAL NOT NULL,
    unit_price      REAL NOT NULL,
    unit_cost       REAL,
    discount_pct    REAL DEFAULT 0,
    subtotal        REAL NOT NULL,       -- qty * price * (1 - discount)
    cost_total      REAL,                -- qty * unit_cost
    gross_profit    REAL,                -- subtotal - cost_total
    margin_pct      REAL,                -- gross_profit / subtotal
    tax_amount      REAL DEFAULT 0,
    total           REAL NOT NULL,
    currency        TEXT DEFAULT 'BOB',
    status          TEXT DEFAULT 'posted' -- draft/posted/cancelled
);

-- CUENTAS POR COBRAR
CREATE TABLE fact_receivables (
    receivable_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id         TEXT REFERENCES dim_time(date_id),
    invoice_number  TEXT,
    odoo_move_id    INTEGER,
    customer_id     INTEGER REFERENCES dim_customers(customer_id),
    seller_id       INTEGER REFERENCES dim_sellers(seller_id),
    invoice_date    DATE NOT NULL,
    due_date        DATE NOT NULL,
    original_amount REAL NOT NULL,
    paid_amount     REAL DEFAULT 0,
    balance         REAL NOT NULL,        -- original - paid
    days_overdue    INTEGER DEFAULT 0,
    aging_bucket    TEXT,                  -- 'current'/'1-30'/'31-60'/'61-90'/'90+'
    status          TEXT,                  -- 'current'/'overdue'/'paid'/'written_off'
    last_payment_date DATE,
    collection_notes TEXT
);

-- CUENTAS POR PAGAR
CREATE TABLE fact_payables (
    payable_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id         TEXT REFERENCES dim_time(date_id),
    invoice_number  TEXT,
    odoo_move_id    INTEGER,
    vendor_id       INTEGER REFERENCES dim_vendors(vendor_id),
    invoice_date    DATE NOT NULL,
    due_date        DATE NOT NULL,
    original_amount REAL NOT NULL,
    paid_amount     REAL DEFAULT 0,
    balance         REAL NOT NULL,
    days_overdue    INTEGER DEFAULT 0,
    aging_bucket    TEXT,
    status          TEXT,
    currency        TEXT DEFAULT 'BOB',
    priority        TEXT DEFAULT 'normal' -- 'critical'/'high'/'normal'/'low'
);

-- INVENTARIO (snapshot diario)
CREATE TABLE fact_inventory (
    inventory_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date   TEXT REFERENCES dim_time(date_id),
    product_id      INTEGER REFERENCES dim_products(product_id),
    warehouse       TEXT DEFAULT 'main',
    qty_on_hand     REAL NOT NULL,
    qty_reserved    REAL DEFAULT 0,
    qty_available   REAL,                 -- on_hand - reserved
    qty_incoming    REAL DEFAULT 0,       -- POs pendientes
    unit_cost       REAL,
    total_value     REAL,                 -- qty_on_hand * unit_cost
    avg_daily_sales REAL,                 -- últimos 30 días
    days_of_stock   REAL,                 -- qty_available / avg_daily_sales
    reorder_point   REAL,
    reorder_qty     REAL,
    rotation_class  TEXT,                 -- 'A'/'B'/'C'/'dead_stock'
    last_sale_date  DATE,
    days_since_last_sale INTEGER
);

-- GASTOS
CREATE TABLE fact_expenses (
    expense_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id         TEXT REFERENCES dim_time(date_id),
    account_id      INTEGER REFERENCES dim_accounts(account_id),
    cost_center_id  INTEGER REFERENCES dim_cost_centers(cost_center_id),
    description     TEXT,
    odoo_move_id    INTEGER,
    amount          REAL NOT NULL,
    budget_amount   REAL,                 -- presupuesto mensual
    variance        REAL,                 -- amount - budget
    variance_pct    REAL,
    category        TEXT,                 -- 'fixed'/'variable'/'semi-variable'
    is_recurring    BOOLEAN DEFAULT 0,
    vendor_id       INTEGER REFERENCES dim_vendors(vendor_id)
);

-- ESTADOS FINANCIEROS (mensual)
CREATE TABLE fact_financials (
    financial_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    period          TEXT NOT NULL,         -- '2026-03'
    year            INTEGER,
    month           INTEGER,
    statement_type  TEXT NOT NULL,         -- 'income_statement' / 'balance_sheet'
    account_id      INTEGER REFERENCES dim_accounts(account_id),
    account_code    TEXT,
    account_name    TEXT,
    parent_group    TEXT,                  -- Grupo principal
    sub_group       TEXT,                  -- Sub-grupo
    amount          REAL NOT NULL,
    prev_period     REAL,                 -- Periodo anterior
    prev_year       REAL,                 -- Mismo periodo año anterior
    budget          REAL,                 -- Presupuesto
    ytd_actual      REAL,                 -- Year-to-date actual
    ytd_budget      REAL                  -- Year-to-date presupuesto
);

-- FLUJO DE CAJA
CREATE TABLE fact_cashflow (
    cashflow_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id         TEXT REFERENCES dim_time(date_id),
    category        TEXT NOT NULL,         -- 'operating'/'investing'/'financing'
    sub_category    TEXT,                  -- 'collections'/'payroll'/'suppliers'/etc.
    description     TEXT,
    inflow          REAL DEFAULT 0,
    outflow         REAL DEFAULT 0,
    net_flow        REAL,                  -- inflow - outflow
    running_balance REAL,
    is_projected    BOOLEAN DEFAULT 0,     -- 0=real, 1=proyectado
    confidence      REAL,                  -- % de confianza si es proyectado
    source          TEXT                   -- 'odoo'/'manual'/'ai_projected'
);

-- ============================================
-- TABLAS DE CONFIGURACIÓN Y SOPORTE
-- ============================================

-- PRESUPUESTOS Y OBJETIVOS
CREATE TABLE config_budgets (
    budget_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    module          TEXT NOT NULL,          -- 'sales'/'expenses'/'cashflow'
    category        TEXT,
    metric          TEXT NOT NULL,          -- 'revenue'/'gross_profit'/'total_expense'
    target_value    REAL NOT NULL,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SUPUESTOS MANUALES (input del usuario via chat)
CREATE TABLE config_assumptions (
    assumption_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    module          TEXT NOT NULL,
    description     TEXT NOT NULL,
    impact_type     TEXT,                   -- 'increase'/'decrease'/'replace'
    impact_value    REAL,
    impact_pct      REAL,
    start_date      DATE,
    end_date        DATE,
    is_active       BOOLEAN DEFAULT 1,
    created_by      TEXT DEFAULT 'user'
);

-- CACHE DE ANÁLISIS IA
CREATE TABLE ai_analysis_cache (
    cache_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    module          TEXT NOT NULL,
    analysis_type   TEXT NOT NULL,          -- 'narrative'/'anomaly'/'forecast'/'alert'
    data_hash       TEXT,                   -- Hash de los datos de entrada
    prompt_used     TEXT,
    response         TEXT NOT NULL,
    tokens_used     INTEGER,
    cost_usd        REAL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP,
    is_valid        BOOLEAN DEFAULT 1
);

-- LOG DE SINCRONIZACIÓN
CREATE TABLE sync_log (
    sync_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,          -- 'odoo'/'excel'/'manual'
    module          TEXT NOT NULL,
    records_synced  INTEGER,
    status          TEXT,                   -- 'success'/'error'/'partial'
    error_message   TEXT,
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    duration_sec    REAL
);

-- HISTORIAL DE CHAT
CREATE TABLE chat_history (
    message_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    role            TEXT NOT NULL,          -- 'user'/'assistant'
    content         TEXT NOT NULL,
    module_context  TEXT,                   -- módulo activo al momento del chat
    tokens_used     INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4 Índices Críticos

```sql
-- Índices para queries frecuentes
CREATE INDEX idx_sales_date ON fact_sales(date_id);
CREATE INDEX idx_sales_product ON fact_sales(product_id);
CREATE INDEX idx_sales_customer ON fact_sales(customer_id);
CREATE INDEX idx_sales_seller ON fact_sales(seller_id);
CREATE INDEX idx_receivables_status ON fact_receivables(status, aging_bucket);
CREATE INDEX idx_receivables_customer ON fact_receivables(customer_id);
CREATE INDEX idx_payables_status ON fact_payables(status, due_date);
CREATE INDEX idx_inventory_product ON fact_inventory(product_id, snapshot_date);
CREATE INDEX idx_inventory_rotation ON fact_inventory(rotation_class);
CREATE INDEX idx_expenses_date ON fact_expenses(date_id, cost_center_id);
CREATE INDEX idx_financials_period ON fact_financials(period, statement_type);
CREATE INDEX idx_cashflow_date ON fact_cashflow(date_id, category);
```

---

## 4. MÓDULOS DEL SISTEMA

### 4.1 Módulo HOME — Executive Summary

**Vista:** Dashboard consolidado con KPIs principales de cada área.

**KPIs en tarjetas:**
- Ventas del mes (vs target, vs mes anterior, vs mismo mes año pasado)
- Margen bruto %
- CxC vencidas total
- CxP próximas a vencer (7 días)
- Nivel de inventario (valor total, items críticos)
- Gastos del mes vs presupuesto
- Utilidad neta del mes
- Saldo de caja actual + proyección 7 días

**Componente IA — "Morning Briefing":**
```
Prompt template:
"Eres el analista financiero ejecutivo de {company_name}. Basándote en estos
datos del día de hoy, genera un briefing ejecutivo de máximo 300 palabras para
el CEO. Prioriza: (1) alertas críticas, (2) oportunidades, (3) tendencias.

DATOS:
{json_with_all_kpis}

SUPUESTOS ACTIVOS:
{active_assumptions}

Responde en español, tono profesional pero directo. Usa bullets para alertas."
```

**Alertas Inteligentes (sidebar):**
- 🔴 Críticas: CxC vencidas >90 días, stock agotado de producto A, gasto >20% sobre presupuesto
- 🟡 Atención: CxP próximas a vencer, margen cayendo, cliente sin comprar >60 días
- 🟢 Positivas: Ventas sobre target, nuevo producto top performer, cash position fuerte

---

### 4.2 Módulo VENTAS

**Sub-secciones:**

**4.2.1 Overview de Ventas**
- Revenue total (mes, trimestre, YTD)
- Gráfico de tendencia mensual (12 meses rolling) con línea de tendencia
- Comparativo vs mismo periodo año anterior
- Velocidad de ventas (revenue/día promedio)

**4.2.2 Por Segmento/Línea/Gama**
- Treemap de revenue por categoría → línea → producto
- Tabla dinámica con filtros (segmento, línea, marca, periodo)
- Análisis de Pareto (80/20) — qué productos generan el 80% del revenue
- Margen bruto por segmento (heatmap)

**4.2.3 Top Rankings**
- Top 10 productos por revenue, por margen, por unidades
- Top 10 clientes por revenue, por frecuencia, por margen
- Top vendedores vs target
- Bottom 10 productos (candidatos a descontinuar)

**4.2.4 Análisis de Rentabilidad**
- Scatter plot: Revenue vs Margen por producto (identificar estrellas y trampas)
- Contribución marginal por línea
- Productos con margen decreciente (tendencia 3 meses)

**4.2.5 Clientes**
- Segmentación RFM (Recency, Frequency, Monetary)
- Clientes nuevos vs recurrentes
- Customer lifetime value estimado
- Churn risk (clientes que bajan frecuencia)

**Componente IA — Análisis de Ventas:**
```
Prompt template:
"Analiza los datos de ventas del periodo {period}. Compara con {previous_period}
y {same_period_last_year}.

DATOS:
{sales_summary_json}
{top_products_json}
{top_customers_json}
{seller_performance_json}

Genera:
1. DIAGNÓSTICO (qué pasó y por qué — máx 150 palabras)
2. ANOMALÍAS detectadas (cambios inusuales en patrones)
3. OPORTUNIDADES (productos/clientes con potencial sub-explotado)
4. RIESGOS (concentración, dependencia, márgenes comprimidos)
5. RECOMENDACIONES ACCIONABLES (3-5 acciones concretas)

Usa datos específicos (números, %, nombres de productos/clientes).
No seas genérico. Sé directo."
```

---

### 4.3 Módulo CUENTAS POR COBRAR (CxC)

**Sub-secciones:**

**4.3.1 Aging Report Visual**
- Stacked bar chart de aging: Vigente / 1-30 / 31-60 / 61-90 / 90+
- Tabla detallada con drill-down por cliente
- Total por bucket en tarjetas

**4.3.2 Alertas de Cobranza**
- 🔴 Facturas vencidas >90 días (riesgo de incobrabilidad)
- 🟡 Facturas vencidas 31-90 días (requiere seguimiento)
- 🟢 Por vencer en próximos 7 días (cobranza preventiva)
- Timeline de vencimientos próximos (calendario visual)

**4.3.3 Análisis por Cliente**
- DSO (Days Sales Outstanding) promedio y por cliente
- Historial de pago por cliente (% pagos a tiempo)
- Exposición: % de CxC concentrada en top 5 clientes
- Credit score interno (basado en historial)

**4.3.4 Tendencias**
- Evolución del aging mix (12 meses)
- Ratio de recuperación mensual
- CxC/Ventas ratio (tendencia)

**Componente IA:**
```
"Analiza la cartera de cuentas por cobrar. Total: {total_receivables}.
Distribución: {aging_distribution}.
Top 10 deudores: {top_debtors}.
DSO actual: {dso_days} días vs industria ~{industry_dso} días.

Genera:
1. ESTADO DE LA CARTERA (salud general — semáforo)
2. CLIENTES CRÍTICOS (quiénes necesitan acción inmediata)
3. RIESGO DE INCOBRABILIDAD (estimación basada en aging)
4. PLAN DE COBRANZA PRIORIZADO (orden de acción)
5. IMPACTO EN FLUJO DE CAJA (proyección de cobros realista)"
```

---

### 4.4 Módulo CUENTAS POR PAGAR (CxP)

**Sub-secciones:**

**4.4.1 Overview**
- Total por pagar (vigente vs vencido)
- Aging chart (mirror de CxC)
- Calendario de pagos próximos (30 días)

**4.4.2 Priorización de Pagos**
- Matriz de prioridad: Urgencia vs Impacto
- Proveedores críticos (que no se pueden atrasar)
- Oportunidades de descuento por pronto pago
- CxP vs Cash disponible

**4.4.3 Análisis por Proveedor**
- DPO (Days Payable Outstanding) por proveedor
- Concentración de pagos
- Historial de pagos (puntualidad)

**Componente IA:**
```
"Analiza cuentas por pagar. Total: {total_payables}. Cash disponible: {cash}.
Pagos próximos 7 días: {upcoming_7d}. Pagos próximos 30 días: {upcoming_30d}.
Proveedores vencidos: {overdue_vendors}.

Genera:
1. DIAGNÓSTICO DE LIQUIDEZ (¿podemos cubrir las obligaciones?)
2. PLAN DE PAGOS PRIORIZADO (qué pagar primero y por qué)
3. RIESGOS (proveedores que pueden cortar suministro)
4. OPORTUNIDADES (descuentos por pronto pago, renegociación)
5. PROYECCIÓN: necesidad de financiamiento si hay gap"
```

---

### 4.5 Módulo INVENTARIOS

**Sub-secciones:**

**4.5.1 Overview**
- Valor total de inventario
- Distribución ABC (Pareto de valor)
- Rotación promedio (días de stock)
- Productos en estado crítico (tarjetas de alerta)

**4.5.2 Análisis de Rotación**
- Clasificación ABC por rotación
- Scatter: Días de stock vs Valor (cuadrantes)
  - Alto valor + Baja rotación = ⚠️ Capital atrapado
  - Alto valor + Alta rotación = ⭐ Core products
  - Bajo valor + Baja rotación = 🗑️ Dead stock candidates
  - Bajo valor + Alta rotación = ✅ Commodities

**4.5.3 Niveles Críticos**
- Productos bajo punto de reorden
- Productos con 0 stock + demanda activa
- Sobre-stock (>90 días de inventario)
- Old stock / Dead stock (sin movimiento >180 días)

**4.5.4 Recomendación de Pedidos**
- Algoritmo de reposición basado en:
  - Promedio móvil de ventas (30/60/90 días)
  - Lead time del proveedor
  - Stock de seguridad (configurable)
  - Estacionalidad detectada
- Tabla de pedido sugerido (producto, cantidad, proveedor, urgencia)

**4.5.5 Proyección de Demanda**
- Forecast simple: Moving average + trend
- Visualización de proyección vs real (últimos 6 meses de validación)
- Ajuste por supuestos manuales (estacionalidad, promociones)

**Componente IA:**
```
"Analiza el inventario actual. Valor total: {total_value}.
Productos activos: {active_count}. Dead stock: {dead_stock_count}/{dead_stock_value}.
Productos bajo reorden: {below_reorder}.
Top 10 por rotación: {top_rotation}. Bottom 10: {bottom_rotation}.

Genera:
1. SALUD DEL INVENTARIO (score general + justificación)
2. ACCIONES INMEDIATAS (qué comprar hoy, qué liquidar)
3. CAPITAL ATRAPADO (cuánto $ está en productos de baja rotación)
4. RECOMENDACIÓN DE PEDIDO (basada en datos, no genérica)
5. ALERTA DE STOCKOUT (qué productos se van a agotar y cuándo)
6. ESTACIONALIDAD detectada (si aplica)"
```

---

### 4.6 Módulo GASTOS

**Sub-secciones:**

**4.6.1 Overview**
- Gasto total del mes vs presupuesto (gauge chart)
- Distribución por categoría (donut chart)
- Tendencia 12 meses
- Varianza presupuestal total

**4.6.2 Análisis por Centro de Costo**
- Tabla: CC → Presupuesto → Real → Varianza → %
- Drill-down por cuenta contable
- Semáforo por centro de costo

**4.6.3 Comportamiento y Tendencias**
- Gastos fijos vs variables (evolución)
- Detección de gastos inusuales (>2σ del promedio)
- Estacionalidad de gastos
- Gasto por empleado (si aplica)

**4.6.4 Presupuesto vs Real**
- Waterfall chart: Presupuesto → Ajustes → Real
- Detalle de desviaciones significativas
- YTD budget consumption rate

**Componente IA:**
```
"Analiza gastos del periodo {period}. Total: {total_expenses} vs Presupuesto: {budget}.
Varianza: {variance} ({variance_pct}%).
Por categoría: {expense_breakdown}.
Gastos inusuales detectados: {anomalies}.

Genera:
1. DIAGNÓSTICO (¿estamos dentro del presupuesto? ¿por qué?)
2. DESVIACIONES IMPORTANTES (cuáles y posibles causas)
3. GASTOS INUSUALES (cualquier anomalía)
4. TENDENCIA (¿estamos gastando más o menos con el tiempo?)
5. RECOMENDACIONES DE OPTIMIZACIÓN (áreas donde reducir sin impacto)"
```

---

### 4.7 Módulo FINANCIERO (Estados Financieros)

**Sub-secciones:**

**4.7.1 Estado de Resultados**
- P&L completo con estructura estándar
- Comparativo: Mes actual vs anterior vs mismo mes año pasado
- Márgenes: Bruto, Operativo, Neto (tarjetas + tendencia)
- Common-size analysis (% sobre ventas)

**4.7.2 Balance General**
- Balance estructurado (Activo / Pasivo / Patrimonio)
- Composición de activos y pasivos (donut charts)
- Evolución trimestral

**4.7.3 Índices Financieros**
```
Operativos:
- Margen Bruto = Utilidad Bruta / Ventas
- Margen Operativo = EBIT / Ventas
- Margen Neto = Utilidad Neta / Ventas
- ROA = Utilidad Neta / Activos Totales
- ROE = Utilidad Neta / Patrimonio

Liquidez:
- Razón Corriente = AC / PC
- Prueba Ácida = (AC - Inventarios) / PC
- Capital de Trabajo = AC - PC
- Cash Ratio = Efectivo / PC

Eficiencia:
- Rotación de Inventarios = Costo Ventas / Inventario Promedio
- DSO = (CxC / Ventas) * 365
- DPO = (CxP / Costo Ventas) * 365
- Ciclo de Conversión de Efectivo = DSO + DIO - DPO

Apalancamiento:
- Deuda/Patrimonio = Pasivo Total / Patrimonio
- Deuda/Activos = Pasivo Total / Activo Total
- Cobertura de Intereses = EBIT / Gastos Financieros

Rentabilidad:
- EBITDA
- EBITDA Margin
- ROI por línea de negocio
```

**4.7.4 Análisis de Tendencia**
- Sparklines de cada índice (12 meses)
- Alertas cuando un índice cruza umbrales definidos
- Benchmarking vs targets internos

**Componente IA:**
```
"Analiza los estados financieros del periodo {period}.

ESTADO DE RESULTADOS:
{income_statement_json}

BALANCE GENERAL:
{balance_sheet_json}

ÍNDICES CALCULADOS:
{ratios_json}

COMPARATIVO:
{comparison_json}

Genera un ANÁLISIS FINANCIERO EJECUTIVO:
1. DIAGNÓSTICO GENERAL (rentabilidad, liquidez, eficiencia — 1 párrafo)
2. FORTALEZAS FINANCIERAS (qué índices están bien y qué significa)
3. SEÑALES DE ALERTA (qué índices se deterioraron y riesgo)
4. ANÁLISIS DE TENDENCIA (dirección de los últimos 3-6 meses)
5. CICLO DE CONVERSIÓN DE EFECTIVO (análisis del CCC)
6. RECOMENDACIONES ESTRATÉGICAS (3-5 acciones con impacto financiero estimado)

Sé preciso con números. Compara con benchmarks típicos del sector comercial B2B."
```

---

### 4.8 Módulo FLUJO DE CAJA

**Sub-secciones:**

**4.8.1 Cash Position Actual**
- Saldo actual
- Inflows/Outflows del día/semana/mes
- Running balance chart (últimos 30 días)

**4.8.2 Proyección de Flujo**
- Proyección a 30/60/90 días basada en:
  - CxC por vencer (con % de probabilidad de cobro por aging)
  - CxP programados
  - Gastos fijos recurrentes
  - Supuestos manuales activos
- Escenario optimista / base / pesimista
- Punto de quiebre: ¿cuándo se acaba el efectivo si no hay cambios?

**4.8.3 Análisis Histórico**
- Patrón estacional de flujo
- Meses de mayor/menor liquidez
- Waterfall mensual (de dónde viene y a dónde va)

**4.8.4 What-If Scenarios**
- Interface para crear escenarios:
  - "¿Qué pasa si las ventas caen 20%?"
  - "¿Qué pasa si un cliente grande retrasa pago 30 días?"
  - "¿Qué pasa si adelanto compras de inventario?"
- Visualización comparativa de escenarios
- Los supuestos se guardan en config_assumptions

**Componente IA:**
```
"Analiza el flujo de caja. Saldo actual: {current_balance}.
Inflows proyectados 30d: {projected_inflows}.
Outflows proyectados 30d: {projected_outflows}.
CxC por cobrar: {receivables_expected}.
CxP por pagar: {payables_due}.

SUPUESTOS ACTIVOS DEL USUARIO:
{active_assumptions}

Genera:
1. POSICIÓN ACTUAL (¿estamos bien de liquidez? ¿por cuánto tiempo?)
2. PROYECCIÓN REALISTA a 30/60/90 días (considerando supuestos)
3. PUNTO CRÍTICO (¿cuándo podríamos tener problemas de caja?)
4. ESCENARIOS (optimista/base/pesimista — con números)
5. RECOMENDACIONES DE TESORERÍA (acciones para optimizar caja)
6. ALERTAS (pagos grandes próximos, gaps de liquidez detectados)"
```

---

### 4.9 Módulo AI CHAT + WHAT-IF

**Funcionalidades del Chat:**

**4.9.1 Chat Conversacional**
- El usuario puede hacer preguntas en lenguaje natural
- El sistema identifica el módulo relevante y consulta datos
- Claude genera respuestas contextualizadas con datos reales

**4.9.2 Input de Supuestos Manuales**
- "Asume que en abril las ventas bajan 15% por temporada baja"
- "Hay una importación grande de $50,000 llegando el 15 de abril"
- "El cliente X nos confirmó que paga el viernes"
- Estos supuestos se guardan y afectan las proyecciones

**4.9.3 Consultas Ad-Hoc**
- "¿Cuál es mi producto más rentable este trimestre?"
- "Compara mis ventas de febrero vs febrero del año pasado"
- "¿Cuánto me debe el cliente ABC y hace cuánto no paga?"
- "¿Cuál sería mi margen si subo precios 5%?"

**4.9.4 What-If Simulator**
- Interface de escenarios con sliders:
  - Variación de ventas (%)
  - Variación de costos (%)
  - Cambio en days of collection
  - Nuevas inversiones
  - Cambios en gastos fijos
- Resultados en tiempo real: impacto en P&L, cash flow, ratios

**Arquitectura del Chat:**
```python
# Pseudocódigo del chat engine
class CEOChatEngine:
    def __init__(self, db, claude_client):
        self.db = db
        self.claude = claude_client
        self.system_prompt = """
        Eres el analista de inteligencia de negocios del CEO Command Center.
        Tienes acceso a TODOS los datos financieros y operativos de la empresa.
        
        REGLAS:
        1. SIEMPRE responde con datos específicos (números, %, fechas)
        2. Si el usuario da un supuesto, confírmalo y explica el impacto
        3. Si detectas un riesgo en la pregunta, menciónalo proactivamente
        4. Sé conciso pero completo
        5. Usa formato con bullets cuando sea apropiado
        6. Si no tienes datos suficientes, dilo y sugiere qué información necesitas
        
        DATOS DISPONIBLES:
        {context_data}
        
        SUPUESTOS ACTIVOS:
        {active_assumptions}
        """
    
    def process_query(self, user_message, active_module):
        # 1. Detectar intención (pregunta / supuesto / what-if / comando)
        # 2. Extraer datos relevantes del DB según intención
        # 3. Construir contexto con datos frescos
        # 4. Enviar a Claude con system prompt + contexto + historial
        # 5. Si es supuesto: guardar en config_assumptions
        # 6. Retornar respuesta + actualizar dashboard si aplica
        pass
```

---

## 5. CONECTOR ODOO (ETL)

### 5.1 Conexión Odoo XML-RPC

```python
# odoo_connector.py — Estructura base
import xmlrpc.client

class OdooConnector:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.uid = None
        self.password = password
        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        self._authenticate(username, password)
    
    def _authenticate(self, username, password):
        self.uid = self.common.authenticate(self.db, username, password, {})
    
    def search_read(self, model, domain, fields, limit=0, offset=0):
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search_read',
            [domain],
            {'fields': fields, 'limit': limit, 'offset': offset}
        )
    
    # Métodos específicos por módulo:
    def get_invoices(self, date_from, date_to):
        """Extrae facturas de venta para fact_sales"""
        pass
    
    def get_receivables(self):
        """Extrae movimientos contables de CxC"""
        pass
    
    def get_payables(self):
        """Extrae movimientos contables de CxP"""
        pass
    
    def get_inventory(self):
        """Extrae stock actual por producto/warehouse"""
        pass
    
    def get_journal_entries(self, date_from, date_to):
        """Extrae asientos contables para gastos y EEFF"""
        pass
    
    def get_products(self):
        """Extrae catálogo de productos"""
        pass
    
    def get_partners(self):
        """Extrae clientes y proveedores"""
        pass
```

### 5.2 Modelos de Odoo a Consultar

| Dato | Modelo Odoo | Campos Clave |
|---|---|---|
| Facturas de Venta | `account.move` + `account.move.line` | partner_id, invoice_date, amount_total, line_ids |
| Productos | `product.product` + `product.template` | name, categ_id, list_price, standard_price |
| Stock | `stock.quant` | product_id, location_id, quantity |
| Clientes/Proveedores | `res.partner` | name, customer_rank, supplier_rank, credit_limit |
| Asientos Contables | `account.move.line` | account_id, debit, credit, date, partner_id |
| Plan de Cuentas | `account.account` | code, name, account_type |
| Pagos | `account.payment` | partner_id, amount, date, payment_type |
| Vendedores | `res.users` / `crm.team` | name, sale_team_id |

### 5.3 Estrategia de Sincronización

```
Frecuencia de Sync:
├── Real-time (cada consulta):  Stock actual, Saldo de caja
├── Cada 15 min:                Facturas nuevas, Pagos recibidos
├── Cada hora:                  CxC aging update, CxP update
├── Diario (noche):             Full sync de todo, Snapshot inventario
└── Mensual:                    Cierre contable, EEFF, Recalculo índices
```

---

## 6. MOTOR DE INTELIGENCIA ARTIFICIAL

### 6.1 Arquitectura del AI Engine

```python
# ai_engine.py — Estructura

class AIEngine:
    """Motor central de IA para CEO Command Center"""
    
    def __init__(self, api_key, db_connection):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.db = db_connection
        self.model = "claude-sonnet-4-20250514"
        self.cache = AICache(db_connection)
    
    # =====================
    # ANÁLISIS NARRATIVO
    # =====================
    def generate_module_analysis(self, module: str, period: str) -> dict:
        """Genera análisis completo para cualquier módulo"""
        data = self._get_module_data(module, period)
        cache_key = self._generate_cache_key(module, period, data)
        
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        prompt = self._build_analysis_prompt(module, data)
        response = self._call_claude(prompt)
        self.cache.set(cache_key, response, ttl_hours=4)
        return response
    
    # =====================
    # DETECCIÓN DE ANOMALÍAS
    # =====================
    def detect_anomalies(self, module: str) -> list:
        """Detecta patrones inusuales usando estadística + IA"""
        # Paso 1: Detección estadística (Z-score, IQR)
        statistical_anomalies = self._statistical_detection(module)
        
        # Paso 2: Contextualización con IA
        if statistical_anomalies:
            context_prompt = f"""
            Se detectaron las siguientes anomalías estadísticas en {module}:
            {json.dumps(statistical_anomalies)}
            
            Para cada una:
            1. ¿Es realmente una anomalía o tiene explicación normal?
            2. Nivel de severidad (critical/warning/info)
            3. Acción recomendada
            """
            return self._call_claude(context_prompt)
        return []
    
    # =====================
    # PROYECCIONES
    # =====================
    def generate_forecast(self, module: str, periods_ahead: int = 3) -> dict:
        """Genera proyecciones combinando estadística + IA"""
        historical = self._get_historical_data(module, lookback_months=12)
        assumptions = self._get_active_assumptions(module)
        
        # Paso 1: Forecast estadístico (baseline)
        statistical_forecast = self._moving_average_forecast(historical, periods_ahead)
        
        # Paso 2: Ajuste con IA (considerando supuestos y contexto)
        adjusted_prompt = f"""
        Forecast estadístico baseline: {json.dumps(statistical_forecast)}
        Datos históricos: {json.dumps(historical)}
        Supuestos del usuario: {json.dumps(assumptions)}
        
        Ajusta el forecast considerando:
        1. Los supuestos manuales
        2. Estacionalidad que detectes en los datos
        3. Tendencias recientes
        
        Retorna JSON con:
        - forecast_optimista, forecast_base, forecast_pesimista
        - confidence_level (%)
        - key_assumptions_used
        """
        return self._call_claude(adjusted_prompt)
    
    # =====================
    # ALERTAS INTELIGENTES
    # =====================
    def generate_alerts(self) -> list:
        """Genera alertas inteligentes cross-módulo"""
        all_data = {
            'sales': self._get_module_summary('sales'),
            'receivables': self._get_module_summary('receivables'),
            'payables': self._get_module_summary('payables'),
            'inventory': self._get_module_summary('inventory'),
            'expenses': self._get_module_summary('expenses'),
            'cashflow': self._get_module_summary('cashflow'),
        }
        
        prompt = f"""
        Analiza estos datos consolidados y genera alertas SOLO si son realmente 
        importantes. No generes alertas triviales.
        
        DATOS: {json.dumps(all_data)}
        
        Para cada alerta, retorna JSON:
        {{
            "level": "critical|warning|info|positive",
            "module": "affected_module",
            "title": "Título corto",
            "description": "Explicación en 1-2 líneas",
            "recommended_action": "Qué hacer",
            "impact": "Impacto estimado si no se actúa"
        }}
        
        Máximo 10 alertas. Ordena por importancia.
        """
        return self._call_claude(prompt)
    
    # =====================
    # WHAT-IF SIMULATOR
    # =====================
    def simulate_scenario(self, scenario: dict) -> dict:
        """Simula un escenario what-if"""
        current_state = self._get_current_financial_state()
        
        prompt = f"""
        Estado financiero actual:
        {json.dumps(current_state)}
        
        Escenario a simular:
        {json.dumps(scenario)}
        
        Calcula el impacto en:
        1. Estado de Resultados (nuevo P&L proyectado)
        2. Flujo de Caja (efecto en los próximos 3 meses)
        3. Índices financieros afectados
        4. Nivel de riesgo del escenario
        
        Retorna análisis estructurado con números específicos.
        """
        return self._call_claude(prompt)
    
    # =====================
    # CHAT CONTEXTUAL
    # =====================
    def chat(self, user_message: str, active_module: str, 
             chat_history: list) -> str:
        """Procesa mensajes del chat con contexto completo"""
        # Detectar intención
        intent = self._detect_intent(user_message)
        
        # Cargar datos relevantes según intención y módulo
        context_data = self._load_context(intent, active_module)
        
        # Construir mensajes para Claude
        messages = self._build_chat_messages(
            user_message, chat_history, context_data, active_module
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=self._get_chat_system_prompt(active_module),
            messages=messages
        )
        
        # Si es supuesto, guardar
        if intent == 'assumption':
            self._save_assumption(user_message, response)
        
        return response.content[0].text
```

### 6.2 Estrategia de Costos de API

```
Estimación de consumo mensual Claude API:
├── Morning Briefing diario:        ~30 calls × $0.003 = $0.09
├── Análisis por módulo (7 mods):   ~210 calls × $0.005 = $1.05
├── Detección de anomalías:         ~30 calls × $0.004 = $0.12
├── Alertas diarias:                ~30 calls × $0.004 = $0.12
├── Chat interactivo:               ~300 calls × $0.003 = $0.90
├── What-If simulations:            ~50 calls × $0.005 = $0.25
├── Forecasts:                      ~20 calls × $0.006 = $0.12
└── TOTAL ESTIMADO:                 ~$2.65/mes (con caching agresivo)

Estrategias de ahorro:
1. Caching agresivo (4-8 horas por análisis)
2. Usar claude-haiku para detección de intenciones
3. Comprimir datos en prompts (solo métricas clave, no raw data)
4. Batch analysis (no regenerar por cada cambio menor)
```

---

## 7. ESTRUCTURA DE ARCHIVOS DEL PROYECTO

```
ceo-command-center/
│
├── README.md                          # Documentación general
├── requirements.txt                   # Dependencias Python
├── .env.example                       # Template de variables de entorno
├── .env                               # (gitignore) Credenciales reales
├── setup.py                           # Script de inicialización
│
├── config/
│   ├── __init__.py
│   ├── settings.py                    # Configuración general
│   ├── odoo_config.py                 # Configuración conexión Odoo
│   └── ai_config.py                   # Configuración Claude API
│
├── database/
│   ├── __init__.py
│   ├── schema.sql                     # DDL completo (CREATE TABLEs)
│   ├── seed_data.sql                  # Datos iniciales (dim_time, etc.)
│   ├── db_manager.py                  # Conexión y operaciones DB
│   └── migrations/                    # Migraciones futuras
│
├── etl/
│   ├── __init__.py
│   ├── odoo_connector.py             # Conector XML-RPC a Odoo
│   ├── file_loader.py                # Carga de Excel/CSV
│   ├── transformers.py               # Transformaciones de datos
│   ├── sync_manager.py               # Orquestador de sincronización
│   └── validators.py                 # Validación de datos
│
├── ai/
│   ├── __init__.py
│   ├── engine.py                     # Motor principal de IA
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── sales_prompts.py          # Templates de prompts - Ventas
│   │   ├── receivables_prompts.py    # Templates - CxC
│   │   ├── payables_prompts.py       # Templates - CxP
│   │   ├── inventory_prompts.py      # Templates - Inventario
│   │   ├── expenses_prompts.py       # Templates - Gastos
│   │   ├── financial_prompts.py      # Templates - Financiero
│   │   ├── cashflow_prompts.py       # Templates - Flujo de Caja
│   │   ├── briefing_prompts.py       # Templates - Morning Briefing
│   │   └── chat_prompts.py           # Templates - Chat
│   ├── anomaly_detector.py           # Detección estadística + IA
│   ├── forecaster.py                 # Proyecciones
│   ├── alert_generator.py            # Sistema de alertas
│   ├── whatif_simulator.py           # Simulador de escenarios
│   ├── chat_engine.py                # Motor de chat
│   └── cache_manager.py              # Cache de respuestas IA
│
├── analytics/
│   ├── __init__.py
│   ├── sales_analytics.py           # Lógica de análisis de ventas
│   ├── receivables_analytics.py     # Lógica de análisis CxC
│   ├── payables_analytics.py        # Lógica de análisis CxP
│   ├── inventory_analytics.py       # Lógica de análisis inventario
│   ├── expense_analytics.py         # Lógica de análisis gastos
│   ├── financial_analytics.py       # Ratios e índices financieros
│   ├── cashflow_analytics.py        # Análisis de flujo de caja
│   └── kpi_calculator.py            # Cálculo centralizado de KPIs
│
├── app/
│   ├── Home.py                       # Página principal (Streamlit entry)
│   ├── components/
│   │   ├── __init__.py
│   │   ├── kpi_cards.py              # Componente de tarjetas KPI
│   │   ├── charts.py                 # Gráficos reutilizables
│   │   ├── tables.py                 # Tablas interactivas
│   │   ├── alerts_panel.py           # Panel de alertas
│   │   ├── ai_analysis_box.py        # Box de análisis IA
│   │   ├── chat_interface.py         # Interface de chat
│   │   ├── file_uploader.py          # Carga de archivos
│   │   ├── whatif_panel.py           # Panel what-if con sliders
│   │   └── sidebar.py                # Sidebar con filtros globales
│   └── pages/
│       ├── 1_Ventas.py
│       ├── 2_Cuentas_por_Cobrar.py
│       ├── 3_Cuentas_por_Pagar.py
│       ├── 4_Inventarios.py
│       ├── 5_Gastos.py
│       ├── 6_Financiero.py
│       ├── 7_Flujo_de_Caja.py
│       └── 8_AI_Chat.py
│
├── tests/
│   ├── __init__.py
│   ├── test_etl.py
│   ├── test_analytics.py
│   ├── test_ai_engine.py
│   └── fixtures/
│       └── sample_data.json          # Datos de prueba
│
└── scripts/
    ├── init_db.py                    # Crear BD e insertar seed data
    ├── generate_demo_data.py         # Generar datos demo para testing
    ├── full_sync.py                  # Sync completo manual
    └── run.sh                        # Script de arranque
```

---

## 8. FASES DE DESARROLLO

### FASE 0: Setup & Foundation (Semana 1)
```
□ Crear estructura de directorios
□ Configurar entorno virtual Python
□ Instalar dependencias (requirements.txt)
□ Crear schema.sql con todas las tablas
□ Script init_db.py para crear BD
□ Script generate_demo_data.py (datos sintéticos realistas)
□ Configurar .env con credenciales
□ Streamlit básico con navegación multi-page
□ Verificar conexión a Claude API (hello world)
```

### FASE 1: Data Layer + Odoo ETL (Semanas 2-3)
```
□ Implementar OdooConnector (XML-RPC)
□ Mapear modelos Odoo → tablas locales
□ ETL de Productos → dim_products
□ ETL de Clientes → dim_customers
□ ETL de Proveedores → dim_vendors
□ ETL de Facturas → fact_sales
□ ETL de CxC → fact_receivables
□ ETL de CxP → fact_payables
□ ETL de Stock → fact_inventory
□ ETL de Asientos → fact_expenses + fact_financials
□ File loader para Excel/CSV
□ Sync manager con scheduling básico
□ Validación y logging de sincronización
```

### FASE 2: Analytics Engine (Semanas 3-4)
```
□ KPI Calculator centralizado
□ Sales analytics (todas las métricas del módulo 4.2)
□ Receivables analytics (aging, DSO, scoring)
□ Payables analytics (aging, DPO, priorización)
□ Inventory analytics (ABC, rotación, reorder)
□ Expense analytics (presupuesto, varianza, tendencia)
□ Financial analytics (todos los ratios del módulo 4.7)
□ Cashflow analytics (proyección, histórico)
```

### FASE 3: AI Engine Core (Semanas 4-5)
```
□ Implementar AIEngine base
□ Sistema de prompts por módulo
□ Cache manager para respuestas IA
□ Análisis narrativo para cada módulo
□ Detección de anomalías (estadística + IA)
□ Sistema de alertas inteligentes
□ Morning Briefing generator
□ Testing de calidad de respuestas IA
```

### FASE 4: Dashboard UI (Semanas 5-7)
```
□ Componentes reutilizables (cards, charts, tables)
□ Página Home con Executive Summary
□ Página Ventas (todas las sub-secciones)
□ Página CxC
□ Página CxP
□ Página Inventarios
□ Página Gastos
□ Página Financiero
□ Página Flujo de Caja
□ Panel de alertas en sidebar
□ AI Analysis Box en cada página
□ Filtros globales (periodo, comparación)
□ Responsive design básico
```

### FASE 5: Chat + What-If (Semanas 7-8)
```
□ Chat engine con detección de intenciones
□ Interface de chat en Streamlit
□ Manejo de supuestos (guardar/activar/desactivar)
□ What-If simulator con sliders
□ Visualización de escenarios
□ Historial de conversaciones
□ Contexto dinámico por módulo activo
```

### FASE 6: Forecasting + Polish (Semanas 8-9)
```
□ Forecast de ventas (MA + trend + estacionalidad)
□ Forecast de flujo de caja
□ Recomendación automática de pedidos
□ Refinamiento de prompts IA (iterar calidad)
□ Optimización de performance
□ Manejo de errores robusto
□ Autenticación básica
□ Documentación de usuario
```

### FASE 7: Testing & Deploy (Semana 10)
```
□ Testing con datos reales de Odoo
□ Validación cruzada de números (Odoo vs Dashboard)
□ Ajuste de umbrales y configuraciones
□ Deploy (Streamlit Cloud / servidor propio)
□ Capacitación de usuarios
□ Feedback loop inicial
```

---

## 9. REQUIREMENTS.TXT

```
# Core
streamlit>=1.38.0
pandas>=2.0.0
numpy>=1.24.0
sqlalchemy>=2.0.0

# Database
# SQLite viene con Python, no requiere instalación

# Odoo Connection
xmlrpc-client  # o usar xmlrpc.client (stdlib)

# AI
anthropic>=0.40.0

# Visualization
plotly>=5.18.0
altair>=5.0.0

# Data Processing
openpyxl>=3.1.0           # Excel read/write
python-dateutil>=2.8.0

# Scheduling
apscheduler>=3.10.0

# Authentication
streamlit-authenticator>=0.3.0

# Utilities
python-dotenv>=1.0.0
hashlib                    # stdlib
loguru>=0.7.0              # Better logging

# Optional - Advanced Analytics
# scikit-learn>=1.3.0      # Para forecast ML avanzado (Fase futura)
# statsmodels>=0.14.0      # Para análisis estadístico (Fase futura)
```

---

## 10. VARIABLES DE ENTORNO (.env)

```bash
# Odoo Connection
ODOO_URL=https://tu-instancia.odoo.com
ODOO_DB=nombre_base_datos
ODOO_USERNAME=admin@empresa.com
ODOO_PASSWORD=tu_password_aqui
ODOO_SYNC_INTERVAL_MIN=15

# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
AI_MODEL=claude-sonnet-4-20250514
AI_CACHE_TTL_HOURS=4
AI_MAX_TOKENS=2000

# Database
DB_PATH=./data/ceo_command_center.db

# App Config
APP_NAME="CEO Command Center"
COMPANY_NAME="Tu Empresa SRL"
DEFAULT_CURRENCY=BOB
FISCAL_YEAR_START_MONTH=1

# Auth
AUTH_SECRET_KEY=tu_secret_key_aqui
```

---

## 11. NOTAS PARA IMPLEMENTACIÓN EN CLAUDE CODE

### Orden de Implementación Recomendado

1. **Empezar por `generate_demo_data.py`** — Generar datos sintéticos realistas que permitan desarrollar y probar TODOS los módulos sin necesidad de conexión a Odoo real. Esto desbloquea el desarrollo paralelo.

2. **Construir de abajo hacia arriba:** DB → ETL → Analytics → AI → UI

3. **Para cada módulo, completar vertical:** No hacer todos los analytics primero y luego toda la UI. Mejor: analytics de ventas → UI de ventas → analytics de CxC → UI de CxC...

4. **Iterar prompts de IA:** Los prompts necesitarán múltiples iteraciones. Separar en archivos facilita esto.

5. **Testing continuo:** Cada componente debe probarse con datos demo antes de avanzar.

### Consideraciones Técnicas para Claude Code

- Usar `st.session_state` para mantener estado entre reruns de Streamlit
- Implementar `@st.cache_data` y `@st.cache_resource` para performance
- El chat requiere `st.chat_message` y `st.chat_input` (Streamlit 1.31+)
- Para gráficos, preferir `st.plotly_chart` con `use_container_width=True`
- SQLite no necesita server — el archivo .db se crea automáticamente
- Las llamadas a Claude API deben ser async-friendly (usar `with st.spinner`)
- Implementar error handling robusto en el conector Odoo (timeouts, retries)

### Datos Demo Sugeridos

Para que el desarrollo sea fluido, generar:
- 200+ productos en 5 categorías, 15 líneas, 8 marcas
- 100+ clientes en 3 segmentos (A/B/C)
- 20+ proveedores
- 5 vendedores con targets
- 24 meses de datos de ventas (para tendencias)
- Aging de CxC con distribución realista
- Inventario con mix de rotación (A/B/C/dead)
- 12 meses de gastos con presupuesto
- EEFF de 12 meses

---

## 12. EVOLUCIÓN FUTURA (Post-MVP)

### Fase 2.0 — Migración Enterprise
- SQLite → PostgreSQL
- Streamlit → React + FastAPI
- Deploy en Docker + Cloud (AWS/GCP)
- Multi-empresa / Multi-usuario con roles

### Fase 2.1 — ML Avanzado
- Forecasting con Prophet / ARIMA / XGBoost
- Clustering de clientes (K-Means)
- Detección de anomalías con Isolation Forest
- NLP para análisis de notas de venta

### Fase 2.2 — Automatización
- Alertas por email/WhatsApp
- Reportes PDF automáticos semanales
- Integración con calendario (reuniones de cobro)
- API para conectar con otros sistemas

### Fase 2.3 — Agentes IA
- Agente de cobranza automático
- Agente de compras (recomendaciones + órdenes)
- Agente de pricing dinámico
- Agente de reportes bajo demanda

---

*Documento generado como blueprint técnico para implementación en Claude Code.*
*Versión 1.0 — Marzo 2026*
