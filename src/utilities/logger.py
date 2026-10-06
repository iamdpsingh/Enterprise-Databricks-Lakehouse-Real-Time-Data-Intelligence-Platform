import logging
import sys
from typing import Any, Dict

import structlog

def setup_logger(name: str = "lakehouse") -> structlog.BoundLogger:
    """Configure and return a structured JSON logger.

    Args:
        name: The name of the logger.

    Returns:
        A structlog bound logger configured for JSON output.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )

    return structlog.get_logger(name)

# Expose a default global logger instance
logger = setup_logger()

def bind_context(**kwargs: Any) -> None:
    """Bind contextual variables to the logger for all subsequent log calls in the current context."""
    structlog.contextvars.bind_contextvars(**kwargs)

def clear_context() -> None:
    """Clear the current logger context."""
    structlog.contextvars.clear_contextvars()
