"""Logging stub (audit v1.1)."""
from __future__ import annotations

import logging

logger = logging.getLogger("vaxgenesis")


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or "vaxgenesis")


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO)
