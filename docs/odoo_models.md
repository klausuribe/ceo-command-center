# Odoo Model → Local Database Mapping

## Connection Method
XML-RPC via `xmlrpc.client` (Python stdlib). Endpoints:
- Auth: `{url}/xmlrpc/2/common` → `authenticate(db, user, pass, {})`
- Data: `{url}/xmlrpc/2/object` → `execute_kw(db, uid, pass, model, method, [domain], {params})`

## Model Mappings

### Products → dim_products
**Odoo Model:** `product.product` (variants) + `product.template` (base)
```python
fields = ['id', 'name', 'default_code', 'categ_id', 'list_price',
          'standard_price', 'active', 'product_tmpl_id']
domain = [('active', '=', True), ('sale_ok', '=', True)]
```
| Odoo Field | Local Column | Notes |
|---|---|---|
| id | odoo_product_id | |
| default_code | sku | |
| name | name | |
| categ_id.name | category | Resolve via product.category |
| (custom/tag) | product_line | May need custom field or categ hierarchy |
| (custom/tag) | brand | May need custom field |
| standard_price | unit_cost | |
| list_price | list_price | |
| computed | margin_pct | (list_price - unit_cost) / list_price |

### Customers & Vendors → dim_customers / dim_vendors
**Odoo Model:** `res.partner`
```python
# Customers
fields = ['id', 'name', 'ref', 'city', 'state_id', 'credit_limit',
          'property_payment_term_id', 'user_id', 'active', 'create_date']
domain = [('customer_rank', '>', 0), ('active', '=', True)]

# Vendors
domain = [('supplier_rank', '>', 0), ('active', '=', True)]
```

### Sales Invoices → fact_sales
**Odoo Model:** `account.move` (header) + `account.move.line` (lines)
```python
# Header
fields = ['id', 'name', 'partner_id', 'invoice_date', 'amount_total',
          'state', 'invoice_user_id', 'currency_id']
domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
          ('invoice_date', '>=', date_from), ('invoice_date', '<=', date_to)]

# Lines (for each invoice)
line_fields = ['product_id', 'quantity', 'price_unit', 'discount',
               'price_subtotal', 'price_total']
line_domain = [('move_id', '=', invoice_id), ('display_type', '=', False)]
```
| Odoo Field | Local Column | Notes |
|---|---|---|
| move.name | invoice_number | |
| move.id | odoo_invoice_id | |
| move.invoice_date | date_id | Format to 'YYYY-MM-DD' |
| move.partner_id | customer_id | Lookup in dim_customers |
| move.invoice_user_id | seller_id | Lookup in dim_sellers |
| line.product_id | product_id | Lookup in dim_products |
| line.quantity | quantity | |
| line.price_unit | unit_price | |
| line.discount | discount_pct | |
| line.price_subtotal | subtotal | |
| product.standard_price * qty | cost_total | Calculate locally |
| subtotal - cost_total | gross_profit | Calculate locally |

### Receivables → fact_receivables
**Odoo Model:** `account.move.line`
```python
fields = ['id', 'move_id', 'partner_id', 'date', 'date_maturity',
          'debit', 'credit', 'amount_residual', 'reconciled']
domain = [('account_id.account_type', '=', 'asset_receivable'),
          ('parent_state', '=', 'posted'),
          ('reconciled', '=', False)]  # Only open items
```
Calculate aging_bucket locally: `days_overdue = (today - due_date).days`

### Payables → fact_payables
**Odoo Model:** `account.move.line`
```python
domain = [('account_id.account_type', '=', 'liability_payable'),
          ('parent_state', '=', 'posted'),
          ('reconciled', '=', False)]
```

### Inventory → fact_inventory
**Odoo Model:** `stock.quant`
```python
fields = ['id', 'product_id', 'location_id', 'quantity', 'reserved_quantity']
domain = [('location_id.usage', '=', 'internal')]  # Only internal locations
```
Calculate avg_daily_sales, days_of_stock, rotation_class locally from fact_sales data.

### Journal Entries → fact_expenses + fact_financials
**Odoo Model:** `account.move.line`
```python
fields = ['id', 'move_id', 'account_id', 'partner_id', 'date',
          'debit', 'credit', 'name', 'analytic_distribution']
domain = [('parent_state', '=', 'posted'),
          ('date', '>=', date_from), ('date', '<=', date_to)]
```
- Filter by account_type='expense' for fact_expenses
- Aggregate by account for fact_financials (monthly)

### Payments → fact_cashflow
**Odoo Model:** `account.payment`
```python
fields = ['id', 'partner_id', 'amount', 'date', 'payment_type',
          'partner_type', 'state', 'journal_id']
domain = [('state', '=', 'posted'),
          ('date', '>=', date_from)]
```
- payment_type='inbound' → inflow (collections)
- payment_type='outbound' → outflow (payments to suppliers)

### Sellers → dim_sellers
**Odoo Model:** `res.users` filtered by sales team
```python
fields = ['id', 'name', 'sale_team_id']
domain = [('sale_team_id', '!=', False)]
```

### Chart of Accounts → dim_accounts
**Odoo Model:** `account.account`
```python
fields = ['id', 'code', 'name', 'account_type', 'group_id']
domain = [('deprecated', '=', False)]
```

## Sync Strategy
| Data | Frequency | Method |
|---|---|---|
| Products/Customers/Vendors | Daily (night) | Full refresh |
| New Invoices | Every 15 min | Delta (by write_date) |
| Open Receivables | Every hour | Full refresh of open items |
| Open Payables | Every hour | Full refresh of open items |
| Stock Quantities | Every 15 min | Full refresh |
| Journal Entries | Daily (night) | Delta by date range |
| Payments | Every 15 min | Delta (by write_date) |

## Delta Sync Pattern
```python
# Use write_date for incremental sync
last_sync = get_last_sync_time(module)
domain.append(('write_date', '>', last_sync.isoformat()))
```

## Error Handling
- Wrap all XML-RPC calls in try/except
- Log to sync_log table with status and error_message
- Implement exponential backoff for connection failures
- Set timeout on xmlrpc.client.ServerProxy (default is too long)
```python
proxy = xmlrpc.client.ServerProxy(url, allow_none=True,
    context=ssl._create_unverified_context())  # If self-signed cert
```
