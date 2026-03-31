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
