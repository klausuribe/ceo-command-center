---
name: build-and-verify
description: >
  Self-correcting build loop that writes code, runs it, catches errors, and fixes them
  iteratively until everything works. Use this skill whenever implementing a new module,
  feature, or file. Triggers on "build", "implement", "create module", "develop",
  "write and test", or any request to create functional code that needs to work correctly.
  ALWAYS use this skill instead of writing code without testing it.
---

# Build and Verify — Self-Correcting Development Loop

You implement code using an iterative build-run-fix loop. NEVER write code and stop.
ALWAYS run it and fix errors until it works.

## Core Loop Pattern

For EVERY piece of code you write, follow this cycle:

```
LOOP (max 10 iterations):
  1. WRITE  → Create or edit the code
  2. RUN    → Execute it (python script, streamlit run, pytest, import check)
  3. CHECK  → Did it run without errors?
     - YES → Print "✅ VERIFIED: [what works]" and EXIT loop
     - NO  → Read the FULL error traceback
  4. DIAGNOSE → Identify root cause from the error
  5. FIX    → Apply the fix
  6. GOTO 2 (run again)
```

## Verification Commands by File Type

Choose the right verification for what you're building:

| File Type | Verification Command |
|---|---|
| Python module | `python -c "from module_name import *; print('OK')"` |
| Database schema | `python scripts/init_db.py && python -c "import sqlite3; c=sqlite3.connect('data/ceo_command_center.db'); print(c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())"` |
| Streamlit page | `timeout 10 streamlit run app/Home.py --server.headless true 2>&1 \| head -20` |
| ETL connector | `python -c "from etl.odoo_connector import OdooConnector; print('OK')"` |
| Analytics module | `python -c "from analytics.sales_analytics import *; print('OK')"` then `pytest tests/ -x -q 2>&1 \| tail -20` |
| AI engine | `python -c "from ai.engine import AIEngine; print('OK')"` |
| Full app check | `cd /path/to/project && python -m py_compile app/Home.py && echo 'COMPILES OK'` |

## Error Handling Rules

1. **Read the FULL traceback** — don't guess. The last line tells you the error type, the lines above tell you where.
2. **Fix ONE error at a time** — don't try to fix multiple issues in one edit.
3. **If same error repeats 3 times** — STOP, rethink the approach entirely. The design might be wrong, not just the code.
4. **Import errors** — check if the package is installed (`pip install X --break-system-packages`) or if the module path is correct.
5. **Streamlit errors** — check `st.session_state` usage, missing `@st.cache_data` on heavy functions, and widget key conflicts.

## Post-Build Checklist

After the loop exits successfully, verify:
- [ ] All imports resolve without errors
- [ ] Functions have type hints and docstrings
- [ ] No hardcoded paths or credentials (use .env)
- [ ] Error handling with try/except on external calls (DB, API, file I/O)
- [ ] Print confirmation: `"✅ MODULE COMPLETE: [module_name] — all checks passed"`

## Example Session

```
> Implementing analytics/sales_analytics.py

[Iteration 1] Writing sales_analytics.py...
[Iteration 1] Running: python -c "from analytics.sales_analytics import SalesAnalytics; print('OK')"
[Iteration 1] ERROR: ModuleNotFoundError: No module named 'database'
[Iteration 1] FIX: Adding sys.path or fixing import to use relative path
[Iteration 2] Running: python -c "from analytics.sales_analytics import SalesAnalytics; print('OK')"
[Iteration 2] ERROR: ImportError: cannot import name 'get_db' from 'database.db_manager'
[Iteration 2] FIX: Function is named 'get_connection', not 'get_db'
[Iteration 3] Running: python -c "from analytics.sales_analytics import SalesAnalytics; print('OK')"
[Iteration 3] OUTPUT: OK
✅ VERIFIED: analytics/sales_analytics.py imports and initializes correctly

Running deeper test: pytest tests/test_sales_analytics.py -x -q
...
✅ MODULE COMPLETE: sales_analytics — all checks passed
```
