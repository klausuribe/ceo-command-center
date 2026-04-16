"""Migrate config_budgets and config_assumptions to production schema.

- config_budgets: adds account_id, source, updated_at + unique index
  (year, month, module, account_id).
- config_assumptions: adds account_id and category columns for
  structured filtering of assumptions to specific accounts/groups.

Safe to run multiple times (idempotent).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from sqlalchemy import text

from database.db_manager import get_engine


BUDGET_COLUMNS: list[tuple[str, str]] = [
    ("account_id", "INTEGER REFERENCES dim_accounts(account_id)"),
    ("source", "TEXT DEFAULT 'manual'"),
    ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
]

ASSUMPTION_COLUMNS: list[tuple[str, str]] = [
    ("account_id", "INTEGER REFERENCES dim_accounts(account_id)"),
    ("category", "TEXT"),
]


def existing_columns(conn, table: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}


def _migrate_table(conn, table: str, columns: list[tuple[str, str]]) -> list[str]:
    cols = existing_columns(conn, table)
    if not cols:
        logger.error(f"{table} does not exist. Run init_db.py first.")
        return []
    added: list[str] = []
    for name, ddl in columns:
        if name not in cols:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
            added.append(name)
    return added


def migrate() -> None:
    engine = get_engine()
    with engine.connect() as conn:
        budget_added = _migrate_table(conn, "config_budgets", BUDGET_COLUMNS)
        assumption_added = _migrate_table(conn, "config_assumptions", ASSUMPTION_COLUMNS)

        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_config_budgets_unique "
            "ON config_budgets(year, month, module, account_id)"
        ))
        conn.commit()

    if budget_added:
        logger.success(f"config_budgets → added: {', '.join(budget_added)}")
    else:
        logger.info("config_budgets already up to date.")

    if assumption_added:
        logger.success(f"config_assumptions → added: {', '.join(assumption_added)}")
    else:
        logger.info("config_assumptions already up to date.")

    logger.success("Unique index idx_config_budgets_unique ensured.")


if __name__ == "__main__":
    migrate()
