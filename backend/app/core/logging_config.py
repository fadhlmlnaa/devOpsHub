import logging
import json
import sys
from datetime import datetime, timezone
from app.core.config import settings


class StructuredJsonFormatter(logging.Formatter):
    """Formatter to produce structured JSON logs suitable for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": settings.APP_ENV,
        }

        # Contextual metadata if attached
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "workspace_id"):
            log_obj["workspace_id"] = record.workspace_id
        if hasattr(record, "server_id"):
            log_obj["server_id"] = record.server_id
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging():
    """Configures application-wide logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove default handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if settings.is_production:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)
