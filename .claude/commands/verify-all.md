---
name: verify-all
description: >
  Run a comprehensive health check on the entire CEO Command Center project.
  Checks all imports, database integrity, API connections, and app startup.
  Use when you want to verify everything works, after completing a phase,
  or when debugging issues. Triggers on "verify", "check all", "health check",
  "does everything work", "test everything".
---

# Verify All — Full System Health Check

Run this after completing any phase to ensure nothing is broken.

## Verification Steps

Execute ALL of these in order. Report results as a checklist.

### 1. Python Environment
```bash
python --version
pip list 2>/dev/null | grep -E "streamlit|pandas|anthropic|plotly|sqlalchemy" || echo "MISSING PACKAGES"
```

### 2. Project Structure
```bash
# Check critical files exist
for f in CLAUDE.md requirements.txt database/schema.sql config/settings.py database/db_manager.py app/Home.py; do
  [ -f "$f" ] && echo "✅ $f" || echo "❌ MISSING: $f"
done
```

### 3. Database
```bash
python -c "
import sqlite3
db = sqlite3.connect('data/ceo_command_center.db')
tables = [r[0] for r in db.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]
expected = ['dim_time','dim_products','dim_customers','dim_vendors','dim_sellers',
            'dim_accounts','fact_sales','fact_receivables','fact_payables',
            'fact_inventory','fact_expenses','fact_financials','fact_cashflow']
for t in expected:
    status = '✅' if t in tables else '❌'
    print(f'{status} Table: {t}')
# Check data exists
for t in expected:
    if t in tables:
        count = db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'   → {t}: {count} rows')
"
```

### 4. Module Imports
```bash
python -c "
modules = [
    'config.settings',
    'database.db_manager',
    'analytics.kpi_calculator',
    'analytics.sales_analytics',
    'analytics.receivables_analytics',
    'analytics.payables_analytics',
    'analytics.inventory_analytics',
    'analytics.expense_analytics',
    'analytics.financial_analytics',
    'analytics.cashflow_analytics',
    'ai.engine',
    'ai.chat_engine',
    'ai.cache_manager',
]
for mod in modules:
    try:
        __import__(mod)
        print(f'✅ {mod}')
    except ImportError as e:
        print(f'❌ {mod}: {e}')
    except Exception as e:
        print(f'⚠️  {mod}: {e}')
"
```

### 5. Claude API Connection
```bash
python -c "
from config.settings import ANTHROPIC_API_KEY
if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != 'sk-ant-xxxxxxxxxxxxx':
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    r = client.messages.create(model='claude-sonnet-4-20250514', max_tokens=10,
        messages=[{'role':'user','content':'Say OK'}])
    print(f'✅ Claude API: {r.content[0].text}')
else:
    print('⚠️  Claude API: No key configured (set ANTHROPIC_API_KEY in .env)')
"
```

### 6. Streamlit App Startup
```bash
timeout 15 streamlit run app/Home.py --server.headless true --server.port 8599 2>&1 | head -20
# Should see "You can now view your Streamlit app" without errors
```

### 7. Summary Report
```
══════════════════════════════════════════
📊 SYSTEM HEALTH CHECK — CEO Command Center
══════════════════════════════════════════
Environment:    ✅/❌
Database:       ✅/❌ (X tables, Y total rows)
Imports:        ✅/❌ (X/Y modules OK)
Claude API:     ✅/⚠️/❌
Streamlit App:  ✅/❌
──────────────────────────────────────────
Overall:        HEALTHY / NEEDS ATTENTION
══════════════════════════════════════════
```

If any step fails, diagnose and offer to fix it using the build-and-verify loop.
