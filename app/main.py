"""Application entrypoint for Gosha MVP.

Phase 1 provides configuration and logging bootstrap only.
"""

from app.config import configure_logging, get_settings


def main() -> None:
    """Load settings and initialize logging."""
    settings = get_settings()
    configure_logging(settings.log_level)


if __name__ == "__main__":
    main()
