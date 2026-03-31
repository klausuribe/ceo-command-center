# CEO Command Center — AI-Powered Business Dashboard

## Project Overview
Web app (Streamlit) that centralizes all business areas (Sales, AR, AP, Inventory, Expenses, Financial Statements, Cash Flow) into one CEO dashboard powered by Claude AI for analysis, anomaly detection, forecasting, and chat.

## Stack
- **Frontend:** Streamlit 1.38+ (multi-page app)
- **Database:** SQLite (star schema)
- **AI Engine:** Claude API (anthropic SDK, model: claude-sonnet-4-20250514)
- **ETL:** Python + Pandas + xmlrpc.client (Odoo connector)
- **Charts:** Plotly (use `st.plotly_chart` with `use_container_width=True`)
- **Language:** All UI in Spanish. Code in English. AI responses in Spanish.

## Project Structure
```
ceo-command-center/
├── CLAUDE.md
├── requirements.txt
├── .env / .env.example
├── config/                  # Settings, Odoo config, AI config
├── database/
│   ├── schema.sql           # Full DDL — see docs/schema.sql
│   ├── db_manager.py        # SQLAlchemy connection + CRUD
│   └── seed_data.sql
├── etl/                     # Odoo connector, file loader, sync manager
├── ai/
│   ├── engine.py            # Main AI engine
│   ├── prompts/             # One file per module (sales_prompts.py, etc.)
│   ├── chat_engine.py       # Conversational chat with context
│   ├── anomaly_detector.py  # Statistical (Z-score) + AI interpretation
│   ├── forecaster.py        # Moving avg + AI adjustment
│   ├── alert_generator.py   # Cross-module intelligent alerts
│   └── cache_manager.py     # SQLite-based response caching (4hr TTL)
├── analytics/               # One file per module (KPI calculations, no AI)
├── app/
│   ├── Home.py              # Streamlit entry point
│   ├── components/          # Reusable UI (kpi_cards, charts, ai_box, chat)
│   └── pages/               # 1_Ventas.py through 8_AI_Chat.py
├── tests/
├── scripts/                 # init_db.py, generate_demo_data.py
└── docs/                    # Detailed specs (read when needed)
    ├── schema.sql           # Complete DDL with all tables + indexes
    ├── project_spec.md      # Full module specifications + prompt templates
    └── odoo_models.md       # Odoo model mappings
```

## Key Architecture Decisions
- Star schema: dim_* tables (time, products, customers, vendors, sellers, accounts) + fact_* tables (sales, receivables, payables, inventory, expenses, financials, cashflow)
- AI caching in `ai_analysis_cache` table to minimize API costs
- User assumptions stored in `config_assumptions` — affect projections
- Chat history persisted in `chat_history` table
- Use `st.session_state` for app state. Use `@st.cache_data` / `@st.cache_resource` for performance.

## Development Phases — Execute in Order

### PHASE 0: Foundation (start here)
1. Create `requirements.txt` — see docs/project_spec.md §9
2. Create `.env.example` with all variables — see docs/project_spec.md §10
3. Create `database/schema.sql` — read full DDL from `docs/schema.sql`
4. Create `scripts/init_db.py` — creates SQLite DB from schema.sql
5. Create `scripts/generate_demo_data.py` — generate 24 months of realistic synthetic data: 200+ products (5 categories, 15 lines, 8 brands), 100+ customers (A/B/C segments), 20+ vendors, 5 sellers, full sales/AR/AP/inventory/expenses/financial/cashflow data
6. Create basic Streamlit app with multi-page navigation (sidebar with 8 pages)
7. Verify Claude API connection (simple hello world test)
**Test:** Run init_db.py → generate_demo_data.py → streamlit run app/Home.py → see empty dashboard skeleton

### PHASE 1: Data Layer + ETL
1. `database/db_manager.py` — SQLAlchemy connection, generic query helpers
2. `etl/odoo_connector.py` — XML-RPC connector with auth, search_read, model-specific extractors. See `docs/odoo_models.md` for field mappings.
3. `etl/file_loader.py` — pandas-based Excel/CSV importer with validation
4. `etl/transformers.py` — data cleaning, type casting, dimension lookups
5. `etl/sync_manager.py` — orchestrate sync by schedule (APScheduler)
**Test:** Connect to Odoo → extract products → verify in SQLite

### PHASE 2: Analytics Engine (pure Python, no AI)
Build one analytics module at a time. Each returns dicts/DataFrames ready for charting.
1. `analytics/kpi_calculator.py` — centralized KPI computation
2. `analytics/sales_analytics.py` — revenue, margins, Pareto, top/bottom rankings, RFM
3. `analytics/receivables_analytics.py` — aging buckets, DSO, credit scoring
4. `analytics/payables_analytics.py` — aging, DPO, payment prioritization
5. `analytics/inventory_analytics.py` — ABC classification, rotation, reorder points, stockout risk
6. `analytics/expense_analytics.py` — budget vs actual, variance, trends
7. `analytics/financial_analytics.py` — all ratios (liquidity, efficiency, leverage, profitability). See docs/project_spec.md §4.7.3 for full ratio list.
8. `analytics/cashflow_analytics.py` — historical patterns, projections
**Test:** Each module should work with demo data and return correct calculations

### PHASE 3: AI Engine
1. `ai/cache_manager.py` — SQLite cache with data hashing and TTL
2. `ai/engine.py` — main class: init anthropic client, call_claude helper with error handling + spinner
3. `ai/prompts/` — one file per module. Read prompt templates from `docs/project_spec.md` (§4.1–4.8). Each prompt must require specific data, not generic analysis.
4. `ai/anomaly_detector.py` — Step 1: statistical Z-score/IQR detection. Step 2: send anomalies to Claude for interpretation and severity rating.
5. `ai/alert_generator.py` — cross-module alerts with levels: critical/warning/info/positive
6. `ai/forecaster.py` — moving average baseline + Claude adjustment with confidence levels
**Test:** Call each AI function with demo data → verify quality of responses

### PHASE 4: Dashboard UI
Build vertical: complete one module (analytics + AI + UI) before moving to next.
1. `app/components/` — reusable components:
   - `kpi_cards.py`: metric card with value, delta, trend arrow
   - `charts.py`: wrapper functions for common Plotly charts
   - `tables.py`: interactive st.dataframe with formatting
   - `alerts_panel.py`: colored alert boxes (🔴🟡🟢)
   - `ai_analysis_box.py`: expandable box showing AI analysis with spinner
   - `sidebar.py`: global filters (period, comparison period)
2. `app/Home.py` — Executive Summary: KPI cards + Morning Briefing (AI) + Alerts
3. `app/pages/1_Ventas.py` through `app/pages/7_Flujo_de_Caja.py`
4. For each page: filters at top → KPI cards → charts → tables → AI analysis box at bottom
**Test:** Full navigation, all charts render, AI analysis loads

### PHASE 5: Chat + What-If
1. `ai/chat_engine.py` — intent detection, context loading per module, assumption saving
2. `app/components/chat_interface.py` — `st.chat_message` + `st.chat_input`
3. `app/components/whatif_panel.py` — sliders for scenario variables, real-time impact calc
4. `app/pages/8_AI_Chat.py` — full chat page with history + assumption management
5. Store assumptions in `config_assumptions`, show active assumptions in sidebar
**Test:** Ask questions in chat → get data-backed answers → save assumptions → verify impact on projections

### PHASE 6: Polish + Deploy
1. Refine AI prompts (iterate on quality)
2. Add `streamlit-authenticator` for basic auth
3. Error handling: try/except on all API calls, Odoo connections
4. Performance: audit cache usage, add missing @st.cache_data
5. Deploy: Streamlit Cloud or `streamlit run` on server

## Skills & Commands

### Custom Skills (`.claude/skills/`)
These skills load automatically when relevant. Use them:
- **build-and-verify**: Self-correcting loop. ALWAYS use when writing any code. Write → Run → Check → Fix → Repeat until ✅.
- **streamlit-dashboard**: Patterns for KPI cards, Plotly charts, page layouts, AI analysis boxes.
- **ai-engine-builder**: Claude API integration, prompt templates, caching, chat engine patterns.
- **etl-pipeline**: Odoo XML-RPC extraction, file loading, sync orchestration.
- **analytics-module**: KPI calculations, financial ratios, aging reports, ABC classification.

### Slash Commands (`.claude/commands/`)
- `/build-phase N`: Execute phase N from the development plan. Reads relevant docs, builds each item with verification.
- `/verify-all`: Full system health check — environment, database, imports, API, app startup.

### External Skill: Streamlit Official
Install the official Streamlit agent skills for best practices:
```bash
cp -r ~/.claude/skills/developing-with-streamlit .claude/skills/  # If installed globally
```
Or clone from: https://github.com/streamlit/agent-skills
This gives sub-skills for: dashboards, chat UI, multipage apps, session state, layouts, performance, themes.

## Build Philosophy
NEVER write code and move on. ALWAYS follow the build-and-verify loop:
1. Write the code
2. Run it (`python -c "import ..."`, `pytest`, `streamlit run`)
3. If error → read traceback → fix → run again
4. Repeat until clean
5. Only then move to the next task

This applies to EVERY file, EVERY function, EVERY module.

## Coding Standards
- Python 3.11+, type hints on all functions
- Docstrings on every public function
- f-strings for formatting, loguru for logging
- Handle errors gracefully — never crash the dashboard
- All database queries through db_manager (never raw sqlite3)
- AI prompts: always require specific data, never generic. Include "Sé directo, usa números específicos" in every prompt.

## Reference Docs (read these when working on specific phases)
- `docs/schema.sql` — Complete database DDL with all tables, indexes, and comments
- `docs/project_spec.md` — Full module specifications, prompt templates, Odoo mappings, requirements.txt, .env variables
- `docs/odoo_models.md` — Odoo model → local table field mapping
