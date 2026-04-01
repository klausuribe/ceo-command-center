"""Central configuration — loads from .env (local) or st.secrets (Streamlit Cloud)."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (local dev)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _get(key: str, default: str = "") -> str:
    """Get config value from st.secrets (Cloud) or env vars (local)."""
    # Try Streamlit secrets first (works on Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)

# --- Odoo ---
ODOO_URL: str = _get("ODOO_URL")
ODOO_DB: str = _get("ODOO_DB")
ODOO_USERNAME: str = _get("ODOO_USERNAME")
ODOO_PASSWORD: str = _get("ODOO_PASSWORD")
ODOO_SYNC_INTERVAL_MIN: int = int(_get("ODOO_SYNC_INTERVAL_MIN", "15"))

# --- Claude API ---
ANTHROPIC_API_KEY: str = _get("ANTHROPIC_API_KEY")
AI_MODEL: str = _get("AI_MODEL", "claude-sonnet-4-20250514")
AI_CACHE_TTL_HOURS: int = int(_get("AI_CACHE_TTL_HOURS", "4"))
AI_MAX_TOKENS: int = int(_get("AI_MAX_TOKENS", "2000"))

# --- Database ---
DB_PATH: str = _get("DB_PATH", str(PROJECT_ROOT / "data" / "ceo_command_center.db"))

# --- App ---
APP_NAME: str = _get("APP_NAME", "CEO Command Center")
COMPANY_NAME: str = _get("COMPANY_NAME", "Tu Empresa SRL")
DEFAULT_CURRENCY: str = _get("DEFAULT_CURRENCY", "BOB")
FISCAL_YEAR_START_MONTH: int = int(_get("FISCAL_YEAR_START_MONTH", "1"))

# --- Auth ---
AUTH_SECRET_KEY: str = _get("AUTH_SECRET_KEY", "change-me")
