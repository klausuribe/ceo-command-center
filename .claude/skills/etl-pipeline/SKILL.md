---
name: etl-pipeline
description: >
  Build ETL pipelines for extracting data from Odoo (XML-RPC), Excel/CSV files,
  and manual inputs, then transforming and loading into the SQLite data warehouse.
  Use this skill whenever working on data extraction, Odoo connection, file loading,
  data sync, transformations, or anything in the etl/ directory. Triggers on "ETL",
  "Odoo", "sync", "extract", "import", "data load", "CSV", "Excel", "connector",
  "XML-RPC", or any data pipeline work.
---

# ETL Pipeline Builder

Build data pipelines that extract from Odoo/files, transform, and load into SQLite.

## Odoo XML-RPC Connection Pattern

```python
import xmlrpc.client

class OdooConnector:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.password = password
        self.common = xmlrpc.client.ServerProxy(
            f'{url}/xmlrpc/2/common', allow_none=True
        )
        self.models = xmlrpc.client.ServerProxy(
            f'{url}/xmlrpc/2/object', allow_none=True
        )
        self.uid = self.common.authenticate(db, username, password, {})
        if not self.uid:
            raise ConnectionError("Odoo authentication failed")

    def search_read(self, model, domain, fields, limit=0, offset=0, order=None):
        params = {'fields': fields, 'limit': limit, 'offset': offset}
        if order:
            params['order'] = order
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_read', [domain], params
            )
        except Exception as e:
            raise ConnectionError(f"Odoo query failed on {model}: {e}")
```

## Key Odoo Models to Extract

Read `docs/odoo_models.md` for complete field mappings. Summary:

| Local Table | Odoo Model | Key Domain Filter |
|---|---|---|
| dim_products | product.product | `[('active','=',True),('sale_ok','=',True)]` |
| dim_customers | res.partner | `[('customer_rank','>',0)]` |
| dim_vendors | res.partner | `[('supplier_rank','>',0)]` |
| fact_sales | account.move + account.move.line | `[('move_type','=','out_invoice'),('state','=','posted')]` |
| fact_receivables | account.move.line | `[('account_id.account_type','=','asset_receivable'),('reconciled','=',False)]` |
| fact_payables | account.move.line | `[('account_id.account_type','=','liability_payable'),('reconciled','=',False)]` |
| fact_inventory | stock.quant | `[('location_id.usage','=','internal')]` |

## Delta Sync Pattern

```python
def sync_delta(self, model, last_sync_time, fields, domain_extra=None):
    """Only fetch records modified since last sync."""
    domain = [('write_date', '>', last_sync_time.isoformat())]
    if domain_extra:
        domain.extend(domain_extra)
    return self.search_read(model, domain, fields)
```

## File Loader Pattern (Excel/CSV)

```python
import pandas as pd

class FileLoader:
    REQUIRED_COLUMNS = {
        'sales': ['fecha', 'producto', 'cliente', 'cantidad', 'precio'],
        'expenses': ['fecha', 'cuenta', 'descripcion', 'monto'],
    }

    def load_file(self, file_path: str, file_type: str) -> pd.DataFrame:
        ext = file_path.rsplit('.', 1)[-1].lower()
        if ext in ('xlsx', 'xls'):
            df = pd.read_excel(file_path)
        elif ext == 'csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # Validate required columns
        df.columns = df.columns.str.strip().str.lower()
        required = self.REQUIRED_COLUMNS.get(file_type, [])
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        return self._clean(df)

    def _clean(self, df):
        df = df.dropna(how='all')
        df = df.drop_duplicates()
        return df
```

## Sync Orchestrator with Logging

```python
from datetime import datetime

class SyncManager:
    def run_sync(self, source, module, sync_fn):
        """Wraps any sync function with logging."""
        started = datetime.now()
        try:
            count = sync_fn()
            self._log(source, module, count, 'success', None, started)
            return count
        except Exception as e:
            self._log(source, module, 0, 'error', str(e), started)
            raise

    def _log(self, source, module, count, status, error, started):
        duration = (datetime.now() - started).total_seconds()
        self.db.execute(
            """INSERT INTO sync_log
               (source, module, records_synced, status, error_message,
                started_at, completed_at, duration_sec)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (source, module, count, status, error,
             started.isoformat(), datetime.now().isoformat(), duration)
        )
        self.db.commit()
```

## Calculated Fields

Some fields are calculated locally after extraction, not from Odoo:

- `fact_receivables.aging_bucket`: Calculate from `(today - due_date).days`
- `fact_inventory.rotation_class`: ABC classification from sales velocity
- `fact_inventory.days_of_stock`: `qty_available / avg_daily_sales`
- `fact_sales.gross_profit`: `subtotal - cost_total`
- `fact_sales.margin_pct`: `gross_profit / subtotal`

## Testing ETL

After building any ETL component:
```bash
# Test Odoo connection (if credentials available)
python -c "
from etl.odoo_connector import OdooConnector
from config.settings import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
odoo = OdooConnector(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
products = odoo.search_read('product.product', [('active','=',True)], ['name'], limit=5)
print(f'Connected. Sample: {products[0][\"name\"]}')
"

# Test file loader
python -c "
from etl.file_loader import FileLoader
loader = FileLoader()
print('FileLoader imports OK')
"

# Test full ETL pipeline (with demo data)
python -c "
from etl.sync_manager import SyncManager
print('SyncManager imports OK')
"
```
