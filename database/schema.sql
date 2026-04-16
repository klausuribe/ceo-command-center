-- ============================================================
-- CEO COMMAND CENTER — Database Schema (SQLite)
-- Star Schema: Dimensions + Facts + Config + Support tables
-- ============================================================

-- ========================
-- DIMENSION TABLES
-- ========================

CREATE TABLE IF NOT EXISTS dim_time (
    date_id         TEXT PRIMARY KEY,       -- '2026-03-24'
    date            DATE NOT NULL,
    day             INTEGER,
    month           INTEGER,
    month_name      TEXT,                   -- 'Enero', 'Febrero', etc.
    quarter         INTEGER,
    year            INTEGER,
    week_number     INTEGER,
    day_of_week     INTEGER,                -- 1=Lunes, 7=Domingo
    is_weekend      BOOLEAN,
    fiscal_year     INTEGER,
    fiscal_quarter  INTEGER
);

CREATE TABLE IF NOT EXISTS dim_products (
    product_id      INTEGER PRIMARY KEY,
    odoo_product_id INTEGER UNIQUE,
    sku             TEXT,
    name            TEXT NOT NULL,
    category        TEXT,                   -- Segmento principal
    product_line    TEXT,                   -- Línea de producto
    brand           TEXT,                   -- Marca/Gama
    unit_cost       REAL,
    list_price      REAL,
    margin_pct      REAL,                   -- (list_price - unit_cost) / list_price
    is_active       BOOLEAN DEFAULT 1,
    last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id     INTEGER PRIMARY KEY,
    odoo_partner_id INTEGER UNIQUE,
    name            TEXT NOT NULL,
    customer_code   TEXT,
    segment         TEXT,                   -- 'A'/'B'/'C' (por volumen de compra)
    city            TEXT,
    region          TEXT,
    credit_limit    REAL,
    payment_terms   TEXT,                   -- '30 días', '60 días', etc.
    assigned_seller TEXT,
    is_active       BOOLEAN DEFAULT 1,
    created_date    DATE,
    last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_vendors (
    vendor_id       INTEGER PRIMARY KEY,
    odoo_partner_id INTEGER UNIQUE,
    name            TEXT NOT NULL,
    vendor_code     TEXT,
    category        TEXT,                   -- Tipo de proveedor
    country         TEXT,
    currency        TEXT DEFAULT 'BOB',
    payment_terms   TEXT,
    lead_time_days  INTEGER,                -- Días de entrega promedio
    is_active       BOOLEAN DEFAULT 1,
    last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_sellers (
    seller_id       INTEGER PRIMARY KEY,
    odoo_user_id    INTEGER UNIQUE,
    name            TEXT NOT NULL,
    team            TEXT,
    region          TEXT,
    target_monthly  REAL,                   -- Meta de ventas mensual
    is_active       BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS dim_accounts (
    account_id      INTEGER PRIMARY KEY,
    odoo_account_id INTEGER UNIQUE,
    code            TEXT NOT NULL,           -- Código contable
    name            TEXT NOT NULL,
    account_type    TEXT,                   -- 'asset'/'liability'/'equity'/'income'/'expense'
    parent_group    TEXT,                   -- Grupo principal del plan de cuentas
    sub_group       TEXT,                   -- Sub-grupo
    is_active       BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS dim_cost_centers (
    cost_center_id  INTEGER PRIMARY KEY,
    code            TEXT,
    name            TEXT NOT NULL,
    department      TEXT,
    responsible     TEXT,
    budget_annual   REAL
);


-- ========================
-- FACT TABLES
-- ========================

-- VENTAS: Granularidad = línea de factura
CREATE TABLE IF NOT EXISTS fact_sales (
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
    subtotal        REAL NOT NULL,          -- qty * price * (1 - discount)
    cost_total      REAL,                   -- qty * unit_cost
    gross_profit    REAL,                   -- subtotal - cost_total
    margin_pct      REAL,                   -- gross_profit / subtotal
    tax_amount      REAL DEFAULT 0,
    total           REAL NOT NULL,
    currency        TEXT DEFAULT 'BOB',
    status          TEXT DEFAULT 'posted'   -- 'draft'/'posted'/'cancelled'
);

-- CUENTAS POR COBRAR: Granularidad = factura pendiente
CREATE TABLE IF NOT EXISTS fact_receivables (
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
    balance         REAL NOT NULL,          -- original - paid
    days_overdue    INTEGER DEFAULT 0,      -- Calculated: today - due_date (if positive)
    aging_bucket    TEXT,                   -- 'current'/'1-30'/'31-60'/'61-90'/'90+'
    status          TEXT,                   -- 'current'/'overdue'/'paid'/'written_off'
    last_payment_date DATE,
    collection_notes TEXT
);

-- CUENTAS POR PAGAR: Granularidad = factura por pagar
CREATE TABLE IF NOT EXISTS fact_payables (
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
    status          TEXT,                   -- 'current'/'overdue'/'paid'
    currency        TEXT DEFAULT 'BOB',
    priority        TEXT DEFAULT 'normal'   -- 'critical'/'high'/'normal'/'low'
);

-- INVENTARIO: Granularidad = snapshot diario por producto
CREATE TABLE IF NOT EXISTS fact_inventory (
    inventory_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date   TEXT REFERENCES dim_time(date_id),
    product_id      INTEGER REFERENCES dim_products(product_id),
    warehouse       TEXT DEFAULT 'main',
    qty_on_hand     REAL NOT NULL,
    qty_reserved    REAL DEFAULT 0,
    qty_available   REAL,                   -- on_hand - reserved
    qty_incoming    REAL DEFAULT 0,         -- POs pendientes
    unit_cost       REAL,
    total_value     REAL,                   -- qty_on_hand * unit_cost
    avg_daily_sales REAL,                   -- Promedio últimos 30 días
    days_of_stock   REAL,                   -- qty_available / avg_daily_sales
    reorder_point   REAL,                   -- Lead time * avg_daily_sales * safety_factor
    reorder_qty     REAL,
    rotation_class  TEXT,                   -- 'A'/'B'/'C'/'dead_stock'
    last_sale_date  DATE,
    days_since_last_sale INTEGER
);

-- GASTOS: Granularidad = asiento contable de gasto
CREATE TABLE IF NOT EXISTS fact_expenses (
    expense_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id         TEXT REFERENCES dim_time(date_id),
    account_id      INTEGER REFERENCES dim_accounts(account_id),
    cost_center_id  INTEGER REFERENCES dim_cost_centers(cost_center_id),
    description     TEXT,
    odoo_move_id    INTEGER,
    amount          REAL NOT NULL,
    budget_amount   REAL,                   -- Presupuesto mensual asignado
    variance        REAL,                   -- amount - budget
    variance_pct    REAL,
    category        TEXT,                   -- 'fixed'/'variable'/'semi-variable'
    is_recurring    BOOLEAN DEFAULT 0,
    vendor_id       INTEGER REFERENCES dim_vendors(vendor_id)
);

-- ESTADOS FINANCIEROS: Granularidad = cuenta contable por periodo mensual
CREATE TABLE IF NOT EXISTS fact_financials (
    financial_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    period          TEXT NOT NULL,           -- '2026-03'
    year            INTEGER,
    month           INTEGER,
    statement_type  TEXT NOT NULL,           -- 'income_statement' / 'balance_sheet'
    account_id      INTEGER REFERENCES dim_accounts(account_id),
    account_code    TEXT,
    account_name    TEXT,
    parent_group    TEXT,
    sub_group       TEXT,
    amount          REAL NOT NULL,
    prev_period     REAL,                   -- Periodo anterior
    prev_year       REAL,                   -- Mismo mes año pasado
    budget          REAL,
    ytd_actual      REAL,                   -- Year-to-date acumulado real
    ytd_budget      REAL                    -- Year-to-date acumulado presupuesto
);

-- FLUJO DE CAJA: Granularidad = movimiento diario por categoría
CREATE TABLE IF NOT EXISTS fact_cashflow (
    cashflow_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id         TEXT REFERENCES dim_time(date_id),
    category        TEXT NOT NULL,           -- 'operating'/'investing'/'financing'
    sub_category    TEXT,                   -- 'collections'/'payroll'/'suppliers'/etc.
    description     TEXT,
    inflow          REAL DEFAULT 0,
    outflow         REAL DEFAULT 0,
    net_flow        REAL,                   -- inflow - outflow
    running_balance REAL,
    is_projected    BOOLEAN DEFAULT 0,      -- 0=real, 1=proyectado
    confidence      REAL,                   -- % de confianza si es proyectado
    source          TEXT                    -- 'odoo'/'manual'/'ai_projected'
);


-- ========================
-- CONFIGURATION TABLES
-- ========================

CREATE TABLE IF NOT EXISTS config_budgets (
    budget_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    module          TEXT NOT NULL,           -- 'sales'/'expenses'/'cashflow'
    account_id      INTEGER REFERENCES dim_accounts(account_id),
    category        TEXT,
    metric          TEXT NOT NULL,           -- 'revenue'/'gross_profit'/'total_expense' o nombre de cuenta
    target_value    REAL NOT NULL,
    source          TEXT DEFAULT 'manual',   -- 'manual'/'projected'/'imported'
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_config_budgets_unique
    ON config_budgets(year, month, module, account_id);

CREATE TABLE IF NOT EXISTS config_assumptions (
    assumption_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    module          TEXT NOT NULL,
    description     TEXT NOT NULL,
    impact_type     TEXT,                   -- 'increase'/'decrease'/'replace'
    impact_value    REAL,
    impact_pct      REAL,
    account_id      INTEGER REFERENCES dim_accounts(account_id),
    category        TEXT,                    -- texto libre para substring match (ej. 'marketing')
    start_date      DATE,
    end_date        DATE,
    is_active       BOOLEAN DEFAULT 1,
    created_by      TEXT DEFAULT 'user'
);


-- ========================
-- SUPPORT TABLES
-- ========================

CREATE TABLE IF NOT EXISTS ai_analysis_cache (
    cache_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    module          TEXT NOT NULL,
    analysis_type   TEXT NOT NULL,           -- 'narrative'/'anomaly'/'forecast'/'alert'
    data_hash       TEXT,                   -- MD5 hash de datos de entrada
    prompt_used     TEXT,
    response        TEXT NOT NULL,
    tokens_used     INTEGER,
    cost_usd        REAL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP,
    is_valid        BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sync_log (
    sync_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,           -- 'odoo'/'excel'/'manual'
    module          TEXT NOT NULL,
    records_synced  INTEGER,
    status          TEXT,                   -- 'success'/'error'/'partial'
    error_message   TEXT,
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    duration_sec    REAL
);

CREATE TABLE IF NOT EXISTS chat_history (
    message_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    role            TEXT NOT NULL,           -- 'user'/'assistant'
    content         TEXT NOT NULL,
    module_context  TEXT,                   -- Módulo activo al chatear
    tokens_used     INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ========================
-- INDEXES
-- ========================

CREATE INDEX IF NOT EXISTS idx_sales_date ON fact_sales(date_id);
CREATE INDEX IF NOT EXISTS idx_sales_product ON fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_seller ON fact_sales(seller_id);
CREATE INDEX IF NOT EXISTS idx_sales_status ON fact_sales(status);

CREATE INDEX IF NOT EXISTS idx_receivables_status ON fact_receivables(status, aging_bucket);
CREATE INDEX IF NOT EXISTS idx_receivables_customer ON fact_receivables(customer_id);
CREATE INDEX IF NOT EXISTS idx_receivables_due ON fact_receivables(due_date);

CREATE INDEX IF NOT EXISTS idx_payables_status ON fact_payables(status, due_date);
CREATE INDEX IF NOT EXISTS idx_payables_vendor ON fact_payables(vendor_id);

CREATE INDEX IF NOT EXISTS idx_inventory_product ON fact_inventory(product_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_inventory_rotation ON fact_inventory(rotation_class);

CREATE INDEX IF NOT EXISTS idx_expenses_date ON fact_expenses(date_id, cost_center_id);
CREATE INDEX IF NOT EXISTS idx_expenses_account ON fact_expenses(account_id);

CREATE INDEX IF NOT EXISTS idx_financials_period ON fact_financials(period, statement_type);
CREATE INDEX IF NOT EXISTS idx_financials_account ON fact_financials(account_id);

CREATE INDEX IF NOT EXISTS idx_cashflow_date ON fact_cashflow(date_id, category);
CREATE INDEX IF NOT EXISTS idx_cashflow_projected ON fact_cashflow(is_projected);

CREATE INDEX IF NOT EXISTS idx_cache_lookup ON ai_analysis_cache(module, analysis_type, data_hash, is_valid);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id, created_at);
