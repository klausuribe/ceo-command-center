"""User lookup — reads the legacy auth_config.yaml so we don't fork credentials.

During Phase 0 the yaml stays the single source of truth. A later phase
will migrate this to a DB-backed users table when we have more than a
handful of accounts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from backend.app.core.config import PROJECT_ROOT


AUTH_CONFIG_PATH = PROJECT_ROOT / "config" / "auth_config.yaml"


@dataclass(frozen=True)
class User:
    username: str
    name: str
    password_hash: str


def get_user(username: str) -> User | None:
    """Return the user record for a given username or None if not found."""
    if not AUTH_CONFIG_PATH.exists():
        return None
    config = yaml.safe_load(AUTH_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    users = (config.get("credentials") or {}).get("usernames") or {}
    record = users.get(username)
    if not record:
        return None
    return User(
        username=username,
        name=record.get("name", username),
        password_hash=record.get("password", ""),
    )
