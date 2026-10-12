"""
Logging configuration for Lakers in 5 data and serving pipeline.
Provides structured JSON and text logging, request/correlation ID propagation,
and sensitive data redaction.
"""

import os
import json
import logging
import contextvars
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Context variable for thread-safe/async-safe request correlation ID
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)

SENSITIVE_KEYS = {
    "password", "secret", "token", "api_key", "apikey", "database_url",
    "authorization", "auth", "credential", "credentials", "connection_string"
}


def get_request_id() -> Optional[str]:
    """Retrieves the current request correlation ID from context."""
    return request_id_ctx.get()


def set_request_id(req_id: str) -> None:
    """Sets the request correlation ID for the current async/thread context."""
    request_id_ctx.set(req_id)


def clear_request_id() -> None:
    """Clears the request correlation ID."""
    request_id_ctx.set(None)


def sanitize_sensitive_data(data: Any) -> Any:
    """Recursively redacts sensitive values from dictionaries and collections."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(s in str(k).lower() for s in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_sensitive_data(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Basic check for URL containing credentials
        if "postgresql://" in data or "postgres://" in data:
            return "[REDACTED_DATABASE_URL]"
        return data
    return data


class StructuredJsonFormatter(logging.Formatter):
    """
    JSON Formatter for container/cloud environments (e.g. Render, GCP, AWS).
    Standardizes log fields and automatically injects request_id and event fields.
    """
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # Request ID from context or record
        req_id = getattr(record, "request_id", None) or get_request_id()
        if req_id:
            payload["request_id"] = req_id

        # Event identifier
        event = getattr(record, "event", None)
        if event:
            payload["event"] = event

        # Extra structured attributes attached to record
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            for k, v in record.extra_fields.items():
                if k not in payload:
                    payload[k] = v

        # Include exception info if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Sanitize sensitive values
        sanitized_payload = sanitize_sensitive_data(payload)
        return json.dumps(sanitized_payload, default=str)


def log_event(
    logger_instance: logging.Logger,
    event: str,
    level: int = logging.INFO,
    message: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Emits a structured event log with standard metadata and correlation ID.
    """
    req_id = kwargs.pop("request_id", None) or get_request_id()
    msg = message or f"Event: {event}"
    extra_fields = sanitize_sensitive_data(kwargs)
    
    extra = {
        "event": event,
        "request_id": req_id,
        "extra_fields": extra_fields
    }
    
    logger_instance.log(level, msg, extra=extra)


def setup_logger(
    name: str = "lakers_in_5",
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    use_json: Optional[bool] = None
) -> logging.Logger:
    """
    Configures and returns a structured logger that writes to console and log files.
    If use_json is True (or LOG_FORMAT=json env var is set), outputs structured JSON.
    """
    logger_obj = logging.getLogger(name)
    if logger_obj.handlers:
        return logger_obj

    logger_obj.setLevel(level)

    # Determine format mode
    is_json = use_json if use_json is not None else (os.getenv("LOG_FORMAT", "").lower() == "json")

    if is_json:
        formatter = StructuredJsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger_obj.addHandler(console_handler)

    # File Handler
    try:
        if log_file is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "ingestion.log")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger_obj.addHandler(file_handler)
    except Exception as e:
        # Gracefully log to standard output if log file creation is not permitted (e.g. read-only container root)
        logger_obj.warning(f"Could not initialize file logger at {log_file}: {e}")

    return logger_obj


logger = setup_logger()

