"""Database connection and query helpers via SQLAlchemy."""

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from loguru import logger

from config.settings import DB_PATH


_engine = None


def get_engine():
    """Return a singleton SQLAlchemy engine for the SQLite database."""
    global _engine
    if _engine is None:
        db_path = Path(DB_PATH).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{db_path}", echo=False)
        logger.info(f"Database engine created: {db_path}")
    return _engine


def execute_sql(sql: str, params: dict[str, Any] | None = None) -> None:
    """Execute a write SQL statement (INSERT, UPDATE, DELETE, DDL)."""
    with get_engine().connect() as conn:
        conn.execute(text(sql), params or {})
        conn.commit()


def execute_script(sql_script: str) -> None:
    """Execute a multi-statement SQL script."""
    with get_engine().connect() as conn:
        for statement in sql_script.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()


def query_df(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Run a SELECT query and return results as a DataFrame."""
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def query_one(sql: str, params: dict[str, Any] | None = None) -> Any:
    """Run a SELECT query and return the first row as a dict, or None."""
    with get_engine().connect() as conn:
        result = conn.execute(text(sql), params or {})
        row = result.mappings().fetchone()
        return dict(row) if row else None


def query_scalar(sql: str, params: dict[str, Any] | None = None) -> Any:
    """Run a SELECT query and return a single scalar value."""
    with get_engine().connect() as conn:
        result = conn.execute(text(sql), params or {})
        row = result.fetchone()
        return row[0] if row else None


def query_df_cached(sql: str, params: dict[str, Any] | None = None, ttl: int = 300) -> pd.DataFrame:
    """Cached version of query_df — use in Streamlit pages for read-heavy queries.

    TTL in seconds (default 5 min). Only works inside a Streamlit app.
    Falls back to regular query_df outside Streamlit.
    """
    try:
        import streamlit as st

        @st.cache_data(ttl=ttl, show_spinner=False)
        def _cached_query(sql_text: str, params_tuple: tuple | None = None) -> pd.DataFrame:
            p = dict(params_tuple) if params_tuple else None
            return query_df(sql_text, p)

        # Convert params dict to tuple for hashing
        params_t = tuple(sorted(params.items())) if params else None
        return _cached_query(sql, params_t)
    except Exception:
        return query_df(sql, params)


def insert_df(df: pd.DataFrame, table: str, if_exists: str = "append") -> int:
    """Insert a DataFrame into a table. Returns number of rows inserted."""
    with get_engine().connect() as conn:
        rows = df.to_sql(table, conn, if_exists=if_exists, index=False)
        conn.commit()
        return rows or 0


def table_count(table: str) -> int:
    """Return row count for a table."""
    return query_scalar(f"SELECT COUNT(*) FROM {table}") or 0
