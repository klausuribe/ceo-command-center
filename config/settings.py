"""Central configuration — loads .env and exposes all settings."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --- Odoo ---
ODOO_URL: str = os.getenv("ODOO_URL", "")
ODOO_DB: str = os.getenv("ODOO_DB", "")
ODOO_USERNAME: str = os.getenv("ODOO_USERNAME", "")
ODOO_PASSWORD: str = os.getenv("ODOO_PASSWORD", "")
ODOO_SYNC_INTERVAL_MIN: int = int(os.getenv("ODOO_SYNC_INTERVAL_MIN", "15"))

# --- Claude API ---
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL: str = os.getenv("AI_MODEL", "claude-sonnet-4-20250514")
AI_CACHE_TTL_HOURS: int = int(os.getenv("AI_CACHE_TTL_HOURS", "4"))
AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "2000"))

# --- Database ---
DB_PATH: str = os.getenv("DB_PATH", str(PROJECT_ROOT / "data" / "ceo_command_center.db"))

# --- App ---
APP_NAME: str = os.getenv("APP_NAME", "CEO Command Center")
COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Tu Empresa SRL")
DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "BOB")
FISCAL_YEAR_START_MONTH: int = int(os.getenv("FISCAL_YEAR_START_MONTH", "1"))

# --- Auth ---
AUTH_SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "change-me")
