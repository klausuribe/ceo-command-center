"""AI response cache backed by SQLite — avoids redundant API calls."""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from loguru import logger
from database.db_manager import execute_sql, query_one, query_scalar
from config.ai_config import CACHE_TTL_HOURS


def _hash_data(data: Any) -> str:
    """MD5 hash of data for cache key."""
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(module: str, analysis_type: str, data: Any) -> str | None:
    """Return cached response if fresh, else None."""
    data_hash = _hash_data(data)
    row = query_one(
        "SELECT response, expires_at FROM ai_analysis_cache "
        "WHERE module = :m AND analysis_type = :t AND data_hash = :h AND is_valid = 1 "
        "ORDER BY created_at DESC LIMIT 1",
        {"m": module, "t": analysis_type, "h": data_hash},
    )
    if row is None:
        return None

    expires = row["expires_at"]
    if expires and datetime.fromisoformat(expires) < datetime.now():
        logger.debug(f"Cache expired for {module}/{analysis_type}")
        return None

    logger.debug(f"Cache hit for {module}/{analysis_type}")
    return row["response"]


def set_cache(
    module: str,
    analysis_type: str,
    data: Any,
    prompt: str,
    response: str,
    tokens_used: int = 0,
    cost_usd: float = 0.0,
) -> None:
    """Store a response in the cache."""
    data_hash = _hash_data(data)
    expires_at = (datetime.now() + timedelta(hours=CACHE_TTL_HOURS)).isoformat()

    execute_sql(
        "INSERT INTO ai_analysis_cache "
        "(module, analysis_type, data_hash, prompt_used, response, "
        "tokens_used, cost_usd, expires_at, is_valid) "
        "VALUES (:module, :type, :hash, :prompt, :response, "
        ":tokens, :cost, :expires, 1)",
        {
            "module": module,
            "type": analysis_type,
            "hash": data_hash,
            "prompt": prompt[:2000],  # Truncate for storage
            "response": response,
            "tokens": tokens_used,
            "cost": cost_usd,
            "expires": expires_at,
        },
    )
    logger.debug(f"Cached {module}/{analysis_type} (expires {expires_at})")


def invalidate(module: str | None = None) -> int:
    """Invalidate cache entries. If module is None, invalidate all."""
    if module:
        execute_sql(
            "UPDATE ai_analysis_cache SET is_valid = 0 WHERE module = :m",
            {"m": module},
        )
    else:
        execute_sql("UPDATE ai_analysis_cache SET is_valid = 0")
    count = query_scalar(
        "SELECT changes()"
    ) or 0
    logger.info(f"Invalidated {count} cache entries" + (f" for {module}" if module else ""))
    return count


def cache_stats() -> dict:
    """Return cache usage statistics."""
    total = query_scalar("SELECT COUNT(*) FROM ai_analysis_cache") or 0
    valid = query_scalar("SELECT COUNT(*) FROM ai_analysis_cache WHERE is_valid = 1") or 0
    total_tokens = query_scalar("SELECT COALESCE(SUM(tokens_used),0) FROM ai_analysis_cache") or 0
    total_cost = query_scalar("SELECT COALESCE(SUM(cost_usd),0) FROM ai_analysis_cache") or 0
    return {
        "total_entries": total,
        "valid_entries": valid,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
    }
