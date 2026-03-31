#!/usr/bin/env python3
"""Initialize the SQLite database from schema.sql."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from database.db_manager import get_engine, execute_script


def init_db() -> None:
    """Create all tables and indexes from schema.sql."""
    schema_path = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
    if not schema_path.exists():
        logger.error(f"schema.sql not found at {schema_path}")
        sys.exit(1)

    schema_sql = schema_path.read_text(encoding="utf-8")

    # Ensure engine is created (creates data/ dir if needed)
    get_engine()
    execute_script(schema_sql)

    # Verify tables were created
    from database.db_manager import query_df
    tables = query_df(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    logger.info(f"Database initialized with {len(tables)} tables:")
    for t in tables["name"]:
        logger.info(f"  ✅ {t}")


if __name__ == "__main__":
    init_db()
