# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

CEO Command Center — AI-powered business intelligence dashboard (Streamlit) that centralizes Sales, AR, AP, Inventory, Expenses, Financial Statements, and Cash Flow. Claude AI provides narrative analysis, anomaly detection, forecasting, alerts, and conversational chat.

## Commands

```bash
# Full startup (creates venv, DB, demo data if missing)
bash scripts/run.sh

# Manual startup
source venv/bin/activate
python scripts/init_db.py              # Create SQLite DB from schema
python scripts/generate_demo_data.py   # 24 months of synthetic data
streamlit run app/Home.py              # Launch dashboard

# Login: ceo / admin123

# Verify everything works
python -c "from analytics.kpi_calculator import all_kpis; print(all_kpis().keys())"
python -c "from ai.engine import get_engine; e = get_engine(); print(e.is_available)"
```

## Stack

- **Frontend:** Streamlit 1.55+ (multi-page, dark theme, `use_container_width=True` on all charts)
- **Database:** SQLite star schema (7 dim + 7 fact + 6 support = 20 tables)
- **AI:** Claude API via `anthropic` SDK, model `claude-sonnet-4-20250514`
- **Charts:** Plotly (wrapped in `app/components/charts.py`)
- **Auth:** streamlit-authenticator, credentials in `config/auth_config.yaml`
- **Language:** UI and AI responses in Spanish. Code and variable names in English.

## Architecture

**Data flow:**
```
Odoo/Excel → etl/ → SQLite → analytics/ (pure Python KPIs) → ai/ (Claude + cache) → app/ (Streamlit)
```

**Three-layer separation:**
1. `analytics/` — Pure computation. One file per module (`sales_analytics.py`, etc.) + `kpi_calculator.py` as the central aggregator. Returns DataFrames/dicts. No AI, no Streamlit.
2. `ai/` — Claude API wrapper with caching. `engine.py` singleton (`get_engine()`), prompt templates in `ai/prompts/`, plus specialized modules: `anomaly_detector.py` (Z-score + AI interpretation), `alert_generator.py` (rule-based + AI-enhanced), `forecaster.py` (moving avg + AI adjustment), `chat_engine.py` (intent detection + context loading), `whatif_simulator.py`.
3. `app/` — Streamlit pages consume analytics + AI. Reusable components in `app/components/`. Every page follows: `set_page_config()` → `require_auth()` → `render_sidebar()` → KPIs → charts → tables → AI analysis box.

**Key patterns:**
- `database/db_manager.py` — All DB access goes through SQLAlchemy helpers (`query_df`, `query_scalar`, `insert_df`). Never use raw sqlite3. Use `query_df_cached()` inside Streamlit pages for auto-caching with 5-min TTL.
- `ai/cache_manager.py` — MD5 hash of input data as cache key, 4-hour TTL, stored in `ai_analysis_cache` table. Always check cache before calling Claude.
- `ai/engine.py` — Singleton via `get_engine()`. Handles rate limits (auto-retry), connection errors, and missing API key gracefully.
- `config_assumptions` table — User assumptions from chat or What-If simulator affect projections system-wide.
- Every AI prompt includes "Sé directo, usa números específicos" — never allow generic analysis.

**Database star schema:**
- Dimensions: `dim_time`, `dim_products`, `dim_customers`, `dim_vendors`, `dim_sellers`, `dim_accounts`, `dim_cost_centers`
- Facts: `fact_sales`, `fact_receivables`, `fact_payables`, `fact_inventory`, `fact_expenses`, `fact_financials`, `fact_cashflow`
- Support: `ai_analysis_cache`, `chat_history`, `sync_log`, `config_assumptions`, `config_budgets`

## Adding a New Page

1. Create `analytics/new_analytics.py` with pure computation functions
2. Create `ai/prompts/new_prompts.py` with prompt template
3. Create `app/pages/N_NewPage.py` following the pattern: `set_page_config` → `require_auth()` → `render_sidebar()` → KPIs → charts → AI box
4. Add navigation link in `app/components/sidebar.py`

## Coding Conventions

- Python 3.12, type hints on all functions
- `loguru` for logging, f-strings for formatting
- Dashboard must never crash — wrap all API/external calls in try/except
- Every Streamlit page must call `require_auth()` immediately after `set_page_config()`
- AI prompts require specific data context (pass real numbers, not placeholders)

## ETL (Not Yet Connected)

Odoo ETL modules in `etl/` are stubbed. When Odoo access becomes available:
- `docs/odoo_models.md` — Complete field mappings for all Odoo models
- `config/odoo_config.py` — Sync schedule per data type
- The app currently runs entirely on demo data from `scripts/generate_demo_data.py`

## Reference Docs

- `docs/schema.sql` — Complete DDL with all tables, indexes, comments
- `docs/project_spec.md` — Full module specs (§4.1–4.9), prompt templates, .env variables, requirements
- `docs/odoo_models.md` — Odoo model → local table field mappings
