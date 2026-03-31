"""Odoo-specific configuration and sync schedule."""

from config.settings import (
    ODOO_URL,
    ODOO_DB,
    ODOO_USERNAME,
    ODOO_PASSWORD,
    ODOO_SYNC_INTERVAL_MIN,
)

# Sync frequency per data type (minutes)
SYNC_SCHEDULE = {
    "products": 1440,        # Daily (night)
    "customers": 1440,       # Daily (night)
    "vendors": 1440,         # Daily (night)
    "invoices": ODOO_SYNC_INTERVAL_MIN,
    "receivables": 60,       # Every hour
    "payables": 60,          # Every hour
    "inventory": ODOO_SYNC_INTERVAL_MIN,
    "journal_entries": 1440, # Daily (night)
    "payments": ODOO_SYNC_INTERVAL_MIN,
}
