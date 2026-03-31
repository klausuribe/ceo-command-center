---
name: analytics-module
description: >
  Build analytics modules that calculate KPIs, financial ratios, rankings, aging reports,
  and business metrics from SQLite data. Use this skill when creating or editing any file
  in the analytics/ directory. Triggers on "analytics", "KPI", "ratio", "metric",
  "calculation", "aging", "ranking", "Pareto", "ABC classification", "DSO", "margin",
  "forecast", "financial analysis", or any business metric computation.
---

# Analytics Module Builder

Build pure-Python analytics that compute business metrics from the SQLite database.

## Module Structure Pattern

Every analytics module follows this pattern:

```python
# analytics/MODULE_analytics.py
import pandas as pd
from database.db_manager import get_connection

class MODULEAnalytics:
    def __init__(self, db=None):
        self.db = db or get_connection()

    def get_summary(self, period: str, comparison: str = None) -> dict:
        """Main entry point: returns all KPIs and data for the dashboard page."""
        return {
            'kpis': self._calculate_kpis(period),
            'trend': self._get_trend(period),
            'ranking': self._get_ranking(period),
            'detail_table': self._get_detail(period),
            'comparison': self._get_comparison(period, comparison) if comparison else None,
        }

    def _query(self, sql: str, params: tuple = ()) -> pd.DataFrame:
        """Execute SQL and return DataFrame."""
        return pd.read_sql_query(sql, self.db, params=params)
```

## Key Formulas by Module

### Sales Analytics
```python
# Pareto (80/20)
def pareto_analysis(self, period):
    df = self._query("SELECT product_name, SUM(subtotal) as revenue FROM fact_sales ...")
    df = df.sort_values('revenue', ascending=False)
    df['cumulative_pct'] = df['revenue'].cumsum() / df['revenue'].sum() * 100
    df['pareto_class'] = df['cumulative_pct'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
    return df
```

### Receivables Analytics
```python
# Aging buckets — recalculate dynamically
def calculate_aging(self):
    df = self._query("SELECT *, julianday('now') - julianday(due_date) as days FROM fact_receivables WHERE status != 'paid'")
    conditions = [
        df['days'] <= 0,
        df['days'].between(1, 30),
        df['days'].between(31, 60),
        df['days'].between(61, 90),
        df['days'] > 90
    ]
    labels = ['Vigente', '1-30 días', '31-60 días', '61-90 días', '90+ días']
    df['aging_bucket'] = pd.cut(df['days'], bins=[-999,0,30,60,90,9999], labels=labels)
    return df

# DSO
def calculate_dso(self, period):
    receivables = self._query("SELECT SUM(balance) FROM fact_receivables WHERE status != 'paid'").iloc[0,0]
    sales_30d = self._query(f"SELECT SUM(subtotal) FROM fact_sales WHERE date_id >= date('now', '-30 days')").iloc[0,0]
    return (receivables / (sales_30d / 30)) if sales_30d else 0
```

### Inventory Analytics
```python
# ABC Classification by value
def abc_classification(self):
    df = self._query("SELECT product_id, total_value, avg_daily_sales FROM fact_inventory WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM fact_inventory)")
    df = df.sort_values('total_value', ascending=False)
    df['cum_pct'] = df['total_value'].cumsum() / df['total_value'].sum() * 100
    df['class'] = df['cum_pct'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
    return df

# Reorder recommendation
def reorder_suggestions(self):
    df = self._query("""
        SELECT i.*, p.name as product_name, v.name as vendor_name, v.lead_time_days
        FROM fact_inventory i
        JOIN dim_products p ON i.product_id = p.product_id
        LEFT JOIN dim_vendors v ON p.product_id = v.vendor_id
        WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_inventory)
        AND i.qty_available <= i.reorder_point
    """)
    df['suggested_qty'] = df['avg_daily_sales'] * (df['lead_time_days'].fillna(15) + 15)  # lead time + 15 days safety
    df['urgency'] = df['days_of_stock'].apply(lambda d: '🔴 Crítico' if d < 7 else ('🟡 Pronto' if d < 15 else '🟢 OK'))
    return df
```

### Financial Analytics — All Ratios
```python
def calculate_ratios(self, period):
    bs = self._get_balance_sheet(period)  # Dict with totals
    pl = self._get_income_statement(period)

    return {
        # Liquidity
        'current_ratio': bs['current_assets'] / bs['current_liabilities'] if bs['current_liabilities'] else 0,
        'quick_ratio': (bs['current_assets'] - bs['inventory']) / bs['current_liabilities'] if bs['current_liabilities'] else 0,
        'cash_ratio': bs['cash'] / bs['current_liabilities'] if bs['current_liabilities'] else 0,
        'working_capital': bs['current_assets'] - bs['current_liabilities'],

        # Profitability
        'gross_margin': pl['gross_profit'] / pl['revenue'] if pl['revenue'] else 0,
        'operating_margin': pl['operating_income'] / pl['revenue'] if pl['revenue'] else 0,
        'net_margin': pl['net_income'] / pl['revenue'] if pl['revenue'] else 0,
        'roa': pl['net_income'] / bs['total_assets'] if bs['total_assets'] else 0,
        'roe': pl['net_income'] / bs['equity'] if bs['equity'] else 0,

        # Efficiency
        'inventory_turnover': pl['cogs'] / bs['avg_inventory'] if bs['avg_inventory'] else 0,
        'dso': (bs['accounts_receivable'] / pl['revenue']) * 365 if pl['revenue'] else 0,
        'dpo': (bs['accounts_payable'] / pl['cogs']) * 365 if pl['cogs'] else 0,
        'ccc': None,  # DSO + DIO - DPO (calculate after)

        # Leverage
        'debt_to_equity': bs['total_liabilities'] / bs['equity'] if bs['equity'] else 0,
        'debt_to_assets': bs['total_liabilities'] / bs['total_assets'] if bs['total_assets'] else 0,
    }
    # CCC
    ratios['dio'] = 365 / ratios['inventory_turnover'] if ratios['inventory_turnover'] else 0
    ratios['ccc'] = ratios['dso'] + ratios['dio'] - ratios['dpo']
    return ratios
```

## Testing Analytics

After building each analytics module:
```bash
python -c "
from analytics.sales_analytics import SalesAnalytics
sa = SalesAnalytics()
summary = sa.get_summary('2026-03')
print(f'KPIs: {list(summary[\"kpis\"].keys())}')
print(f'Trend rows: {len(summary[\"trend\"])}')
print('✅ SalesAnalytics works')
"
```

## Rules
- NEVER call Claude API from analytics modules — pure data computation only
- ALWAYS return dicts or DataFrames (not formatted strings)
- ALWAYS handle division by zero (`if denominator else 0`)
- ALWAYS handle empty DataFrames (`if df.empty: return default`)
- Format numbers in the UI layer, not here
