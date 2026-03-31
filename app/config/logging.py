"""Logging setup for the Gosha app."""

import logging


def configure_logging(log_level: str) -> None:
    """Configure root logging with a compact format."""
    logging.basicConfig(
        level=log_level.upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
