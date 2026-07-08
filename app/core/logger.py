import logging
import sys
import os

import structlog

from app.core.config import settings


# FORCE UTF-8
os.environ["PYTHONIOENCODING"] = "utf-8"

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def setup_logger() -> structlog.stdlib.BoundLogger:

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        encoding="utf-8",   # IMPORTANT
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(
                ensure_ascii=False  # IMPORTANT
            ),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    return structlog.get_logger()


logger = setup_logger()