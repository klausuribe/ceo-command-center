"""Centralized loguru configuration with file rotation."""

import os
import sys
from pathlib import Path

from loguru import logger


def setup_logging() -> None:
    """Configure loguru with console + optional file output."""
    # Remove default handler to avoid duplicates
    logger.remove()

    log_level = os.getenv("LOG_LEVEL", "INFO")

    # Console output
    logger.add(
        sys.stderr,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> — "
            "<level>{message}</level>"
        ),
    )

    # File output (opt-in via LOG_FILE env var)
    log_file = os.getenv("LOG_FILE")
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_path),
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} — {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )


setup_logging()
