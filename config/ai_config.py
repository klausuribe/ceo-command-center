"""AI engine configuration."""

from config.settings import AI_MODEL, AI_CACHE_TTL_HOURS, AI_MAX_TOKENS

# Model settings
MODEL = AI_MODEL
MAX_TOKENS = AI_MAX_TOKENS
CACHE_TTL_HOURS = AI_CACHE_TTL_HOURS

# Alert severity levels
ALERT_LEVELS = ["critical", "warning", "info", "positive"]

# Anomaly detection thresholds
Z_SCORE_THRESHOLD = 2.5
IQR_MULTIPLIER = 1.5

# Alert thresholds (used in alert_generator.py)
ALERT_THRESHOLDS = {
    "receivables_over_90_days": True,      # Alert if any balance >90 days
    "dso_warning_days": 60,                # DSO above this triggers warning
    "concentration_pct": 50,               # Top-5 concentration above this %
    "expense_variance_over_pct": 10,       # Over-budget % for warning
    "expense_variance_under_pct": -5,      # Under-budget % for positive alert
    "mom_change_pct": 15,                  # MoM change above this triggers alert
    "cash_runway_critical_days": 30,       # Runway below this triggers critical
}
