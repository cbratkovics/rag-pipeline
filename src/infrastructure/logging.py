"""Structured logging configuration with correlation IDs."""

import sys
import uuid
from contextvars import ContextVar
from typing import Any, cast

import structlog
from structlog.processors import CallsiteParameter, CallsiteParameterAdder
from structlog.stdlib import BoundLogger

from src.core.config import get_settings

# Context variable for correlation ID
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def add_correlation_id(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add correlation ID to log events."""
    correlation_id = correlation_id_var.get()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_app_context(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add application context to log events."""
    settings = get_settings()
    event_dict["app_name"] = settings.app_name
    event_dict["app_env"] = settings.app_env
    event_dict["deployment_version"] = settings.deployment_version
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.FILENAME,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ]
        ),
        add_correlation_id,
        add_app_context,
    ]

    renderer: structlog.dev.ConsoleRenderer | structlog.processors.JSONRenderer
    if settings.debug:
        # Development: Pretty console output
        renderer = structlog.dev.ConsoleRenderer()
    else:
        # Production: JSON output
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],  # type: ignore[arg-type]
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    import logging.config

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": renderer,
                    "foreign_pre_chain": shared_processors,
                },
            },
            "handlers": {
                "default": {
                    "level": settings.log_level,
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "json",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": settings.log_level,
                    "propagate": True,
                },
                "uvicorn.access": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    )


def get_logger(name: str) -> BoundLogger:
    """Get a structured logger instance."""
    return cast(BoundLogger, structlog.get_logger(name))


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str | None = None) -> str:
    """Set correlation ID for the current context."""
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str | None:
    """Get the current correlation ID."""
    return correlation_id_var.get()


class LoggerMixin:
    """Mixin class to add logging capabilities."""

    @property
    def logger(self) -> BoundLogger:
        """Get logger for the class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
