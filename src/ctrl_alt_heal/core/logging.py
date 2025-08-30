"""Advanced logging system for Ctrl-Alt-Heal application."""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, UTC
from functools import wraps
from typing import Any, Dict, Optional, Callable
import threading

from ctrl_alt_heal.core.interfaces import LoggingService
from ctrl_alt_heal.utils.exceptions import CtrlAltHealException


class StructuredLogger(LoggingService):
    """Structured logging service with correlation IDs and performance tracking."""

    def __init__(self, logger_name: str = "ctrl_alt_heal"):
        self.logger = logging.getLogger(logger_name)
        self._local = threading.local()
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Add handler if not already present
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.INFO)

    def _get_correlation_id(self) -> str:
        """Get current correlation ID or generate new one."""
        if not hasattr(self._local, "correlation_id"):
            self._local.correlation_id = str(uuid.uuid4())
        return self._local.correlation_id

    def _set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current thread."""
        self._local.correlation_id = correlation_id

    def _format_log_entry(
        self, level: str, message: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format log entry as structured JSON."""
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            "message": message,
            "correlation_id": self._get_correlation_id(),
            "thread_id": threading.get_ident(),
        }

        if context:
            log_entry["context"] = context

        return json.dumps(log_entry)

    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        log_entry = self._format_log_entry("INFO", message, context)
        self.logger.info(log_entry)

    def log_warning(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log warning message."""
        log_entry = self._format_log_entry("WARNING", message, context)
        self.logger.warning(log_entry)

    def log_error(
        self,
        message: str,
        error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log error message."""
        if context is None:
            context = {}

        if error:
            context["error_type"] = type(error).__name__
            context["error_message"] = str(error)

            if isinstance(error, CtrlAltHealException):
                context["error_details"] = error.details

        log_entry = self._format_log_entry("ERROR", message, context)
        self.logger.error(log_entry)

    def log_audit(
        self, action: str, user_id: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log audit event."""
        context = {
            "audit_action": action,
            "user_id": user_id,
            "audit_timestamp": datetime.now(UTC).isoformat(),
        }

        if details:
            context["audit_details"] = details  # type: ignore

        log_entry = self._format_log_entry("AUDIT", f"Audit: {action}", context)
        self.logger.info(log_entry)

    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log performance metric."""
        if context is None:
            context = {}

        context["operation"] = operation
        context["duration_ms"] = duration_ms
        context["performance_timestamp"] = datetime.now(UTC).isoformat()

        # Determine log level based on duration
        if duration_ms > 5000:  # 5 seconds
            level = "ERROR"
        elif duration_ms > 1000:  # 1 second
            level = "WARNING"
        else:
            level = "INFO"

        log_entry = self._format_log_entry(level, f"Performance: {operation}", context)
        getattr(self.logger, level.lower())(log_entry)

    def start_correlation(self, correlation_id: Optional[str] = None) -> str:
        """Start a new correlation context."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        self._set_correlation_id(correlation_id)
        return correlation_id

    def get_correlation_id(self) -> str:
        """Get current correlation ID."""
        return self._get_correlation_id()


class PerformanceTracker:
    """Performance tracking decorator and context manager."""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    def track(self, operation_name: str):
        """Decorator to track performance of a function."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    self.logger.log_performance(operation_name, duration_ms)
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    self.logger.log_performance(
                        operation_name, duration_ms, {"error": str(e)}
                    )
                    raise

            return wrapper

        return decorator

    @contextmanager
    def track_operation(
        self, operation_name: str, context: Optional[Dict[str, Any]] = None
    ):
        """Context manager to track performance of a code block."""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            if context is None:
                context = {}
            context["error"] = str(e)
            self.logger.log_performance(operation_name, duration_ms, context)
            raise
        else:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_performance(operation_name, duration_ms, context)


class AuditLogger:
    """Audit logging for compliance and security."""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log user action for audit purposes."""
        audit_details = {
            "resource": resource,
            "action_type": "user_action",
        }

        if details:
            audit_details.update(details)

        self.logger.log_audit(action, user_id, audit_details)

    def log_data_access(
        self,
        user_id: str,
        data_type: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log data access for audit purposes."""
        audit_details = {
            "data_type": data_type,
            "operation": operation,
            "action_type": "data_access",
        }

        if details:
            audit_details.update(details)

        self.logger.log_audit(f"Data {operation}", user_id, audit_details)

    def log_security_event(
        self, user_id: str, event_type: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security events."""
        audit_details = {
            "event_type": event_type,
            "action_type": "security_event",
        }

        if details:
            audit_details.update(details)

        self.logger.log_audit(f"Security: {event_type}", user_id, audit_details)


class CorrelationContext:
    """Context manager for correlation ID management."""

    def __init__(self, logger: StructuredLogger, correlation_id: Optional[str] = None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.previous_correlation_id: Optional[str] = None

    def __enter__(self):
        # Store previous correlation ID
        self.previous_correlation_id = self.logger.get_correlation_id()

        # Set new correlation ID
        if self.correlation_id:
            self.logger.start_correlation(self.correlation_id)
        else:
            self.logger.start_correlation()

        return self.logger.get_correlation_id()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous correlation ID
        if self.previous_correlation_id:
            self.logger.start_correlation(self.previous_correlation_id)


# Global logger instance
_logger = StructuredLogger()
_performance_tracker = PerformanceTracker(_logger)
_audit_logger = AuditLogger(_logger)


def get_logger() -> StructuredLogger:
    """Get the global logger instance."""
    return _logger


def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker."""
    return _performance_tracker


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger."""
    return _audit_logger


def correlation_context(correlation_id: Optional[str] = None):
    """Decorator to add correlation context to a function."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with CorrelationContext(_logger, correlation_id):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def log_performance(operation_name: str):
    """Decorator to log performance of a function."""
    return _performance_tracker.track(operation_name)


def log_audit_event(
    action: str, user_id: str, details: Optional[Dict[str, Any]] = None
):
    """Decorator to log audit events."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                _audit_logger.log_user_action(user_id, action, func.__name__, details)
                return result
            except Exception as e:
                _audit_logger.log_security_event(
                    user_id, f"Error in {action}", {"error": str(e)}
                )
                raise

        return wrapper

    return decorator
