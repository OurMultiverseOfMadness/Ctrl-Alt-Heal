"""Tests for advanced logging system."""

import json
import pytest
from unittest.mock import patch

from ctrl_alt_heal.core.logging import (
    StructuredLogger,
    PerformanceTracker,
    AuditLogger,
    CorrelationContext,
    get_logger,
    get_performance_tracker,
    get_audit_logger,
    correlation_context,
    log_performance,
    log_audit_event,
)
from ctrl_alt_heal.utils.exceptions import ValidationError


class TestStructuredLogger:
    """Test structured logger."""

    def test_logger_creation(self):
        """Test creating a structured logger."""
        logger = StructuredLogger("test_logger")
        assert logger is not None

    def test_log_info(self):
        """Test logging info message."""
        logger = StructuredLogger("test_logger")

        with patch.object(logger.logger, "info") as mock_info:
            logger.log_info("Test message")
            mock_info.assert_called_once()

            # Check that the logged message is valid JSON
            call_args = mock_info.call_args[0][0]
            log_entry = json.loads(call_args)
            assert log_entry["level"] == "INFO"
            assert log_entry["message"] == "Test message"
            assert "correlation_id" in log_entry
            assert "timestamp" in log_entry

    def test_log_warning(self):
        """Test logging warning message."""
        logger = StructuredLogger("test_logger")

        with patch.object(logger.logger, "warning") as mock_warning:
            logger.log_warning("Test warning")
            mock_warning.assert_called_once()

            call_args = mock_warning.call_args[0][0]
            log_entry = json.loads(call_args)
            assert log_entry["level"] == "WARNING"
            assert log_entry["message"] == "Test warning"

    def test_log_error(self):
        """Test logging error message."""
        logger = StructuredLogger("test_logger")

        with patch.object(logger.logger, "error") as mock_error:
            error = ValidationError("Test error", "field", "value")
            logger.log_error("Test error", error)
            mock_error.assert_called_once()

            call_args = mock_error.call_args[0][0]
            log_entry = json.loads(call_args)
            assert log_entry["level"] == "ERROR"
            assert log_entry["message"] == "Test error"
            assert log_entry["context"]["error_type"] == "ValidationError"
            assert log_entry["context"]["error_message"] == "Test error"

    def test_log_audit(self):
        """Test logging audit event."""
        logger = StructuredLogger("test_logger")

        with patch.object(logger.logger, "info") as mock_info:
            logger.log_audit("user_login", "user123", {"ip": "192.168.1.1"})
            mock_info.assert_called_once()

            call_args = mock_info.call_args[0][0]
            log_entry = json.loads(call_args)
            assert log_entry["level"] == "AUDIT"
            assert "Audit: user_login" in log_entry["message"]
            assert log_entry["context"]["audit_action"] == "user_login"
            assert log_entry["context"]["user_id"] == "user123"

    def test_log_performance(self):
        """Test logging performance metrics."""
        logger = StructuredLogger("test_logger")

        with patch.object(logger.logger, "info") as mock_info:
            logger.log_performance("test_operation", 500.0)
            mock_info.assert_called_once()

            call_args = mock_info.call_args[0][0]
            log_entry = json.loads(call_args)
            assert log_entry["level"] == "INFO"
            assert "Performance: test_operation" in log_entry["message"]
            assert log_entry["context"]["operation"] == "test_operation"
            assert log_entry["context"]["duration_ms"] == 500.0

    def test_log_performance_slow_operation(self):
        """Test logging slow performance as warning."""
        logger = StructuredLogger("test_logger")

        with patch.object(logger.logger, "warning") as mock_warning:
            logger.log_performance("slow_operation", 1500.0)
            mock_warning.assert_called_once()

            call_args = mock_warning.call_args[0][0]
            log_entry = json.loads(call_args)
            assert log_entry["level"] == "WARNING"

    def test_log_performance_very_slow_operation(self):
        """Test logging very slow performance as error."""
        logger = StructuredLogger("test_logger")

        with patch.object(logger.logger, "error") as mock_error:
            logger.log_performance("very_slow_operation", 6000.0)
            mock_error.assert_called_once()

            call_args = mock_error.call_args[0][0]
            log_entry = json.loads(call_args)
            assert log_entry["level"] == "ERROR"

    def test_correlation_id_management(self):
        """Test correlation ID management."""
        logger = StructuredLogger("test_logger")

        # Get initial correlation ID
        initial_id = logger.get_correlation_id()
        assert initial_id is not None

        # Start new correlation
        new_id = logger.start_correlation("test_correlation")
        assert new_id == "test_correlation"
        assert logger.get_correlation_id() == "test_correlation"

        # Start auto-generated correlation
        auto_id = logger.start_correlation()
        assert auto_id is not None
        assert auto_id != "test_correlation"


class TestPerformanceTracker:
    """Test performance tracker."""

    def test_performance_tracker_creation(self):
        """Test creating a performance tracker."""
        logger = StructuredLogger("test_logger")
        tracker = PerformanceTracker(logger)
        assert tracker is not None

    def test_track_decorator_success(self):
        """Test performance tracking decorator on successful function."""
        logger = StructuredLogger("test_logger")
        tracker = PerformanceTracker(logger)

        with patch.object(logger, "log_performance") as mock_log:

            @tracker.track("test_operation")
            def test_function():
                return "success"

            result = test_function()
            assert result == "success"
            mock_log.assert_called_once()

            call_args = mock_log.call_args
            assert call_args[0][0] == "test_operation"
            assert call_args[0][1] >= 0  # Duration should be non-negative

    def test_track_decorator_exception(self):
        """Test performance tracking decorator on function that raises exception."""
        logger = StructuredLogger("test_logger")
        tracker = PerformanceTracker(logger)

        with patch.object(logger, "log_performance") as mock_log:

            @tracker.track("test_operation")
            def test_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError):
                test_function()

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == "test_operation"
            assert call_args[0][1] >= 0  # Duration should be non-negative
            assert call_args[0][2]["error"] == "Test error"

    def test_track_operation_context_manager(self):
        """Test performance tracking context manager."""
        logger = StructuredLogger("test_logger")
        tracker = PerformanceTracker(logger)

        with patch.object(logger, "log_performance") as mock_log:
            with tracker.track_operation("test_operation"):
                pass  # Do nothing

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == "test_operation"


class TestAuditLogger:
    """Test audit logger."""

    def test_audit_logger_creation(self):
        """Test creating an audit logger."""
        logger = StructuredLogger("test_logger")
        audit_logger = AuditLogger(logger)
        assert audit_logger is not None

    def test_log_user_action(self):
        """Test logging user action."""
        logger = StructuredLogger("test_logger")
        audit_logger = AuditLogger(logger)

        with patch.object(logger, "log_audit") as mock_audit:
            audit_logger.log_user_action(
                "user123", "login", "auth_system", {"ip": "192.168.1.1"}
            )
            mock_audit.assert_called_once()

            call_args = mock_audit.call_args
            assert call_args[0][0] == "login"
            assert call_args[0][1] == "user123"
            assert call_args[0][2]["resource"] == "auth_system"
            assert call_args[0][2]["action_type"] == "user_action"
            assert call_args[0][2]["ip"] == "192.168.1.1"

    def test_log_data_access(self):
        """Test logging data access."""
        logger = StructuredLogger("test_logger")
        audit_logger = AuditLogger(logger)

        with patch.object(logger, "log_audit") as mock_audit:
            audit_logger.log_data_access(
                "user123", "prescriptions", "read", {"prescription_id": "presc123"}
            )
            mock_audit.assert_called_once()

            call_args = mock_audit.call_args
            assert call_args[0][0] == "Data read"
            assert call_args[0][1] == "user123"
            assert call_args[0][2]["data_type"] == "prescriptions"
            assert call_args[0][2]["operation"] == "read"
            assert call_args[0][2]["action_type"] == "data_access"

    def test_log_security_event(self):
        """Test logging security event."""
        logger = StructuredLogger("test_logger")
        audit_logger = AuditLogger(logger)

        with patch.object(logger, "log_audit") as mock_audit:
            audit_logger.log_security_event(
                "user123", "failed_login", {"ip": "192.168.1.1"}
            )
            mock_audit.assert_called_once()

            call_args = mock_audit.call_args
            assert call_args[0][0] == "Security: failed_login"
            assert call_args[0][1] == "user123"
            assert call_args[0][2]["event_type"] == "failed_login"
            assert call_args[0][2]["action_type"] == "security_event"


class TestCorrelationContext:
    """Test correlation context manager."""

    def test_correlation_context(self):
        """Test correlation context manager."""
        logger = StructuredLogger("test_logger")

        initial_id = logger.get_correlation_id()

        with CorrelationContext(logger, "test_correlation"):
            assert logger.get_correlation_id() == "test_correlation"

        # Should restore previous correlation ID
        assert logger.get_correlation_id() == initial_id

    def test_correlation_context_auto_generated(self):
        """Test correlation context with auto-generated ID."""
        logger = StructuredLogger("test_logger")

        initial_id = logger.get_correlation_id()

        with CorrelationContext(logger):
            new_id = logger.get_correlation_id()
            assert new_id != initial_id
            assert new_id is not None

        # Should restore previous correlation ID
        assert logger.get_correlation_id() == initial_id


class TestGlobalFunctions:
    """Test global logging functions."""

    def test_get_logger(self):
        """Test getting global logger."""
        logger = get_logger()
        assert isinstance(logger, StructuredLogger)

    def test_get_performance_tracker(self):
        """Test getting global performance tracker."""
        tracker = get_performance_tracker()
        assert isinstance(tracker, PerformanceTracker)

    def test_get_audit_logger(self):
        """Test getting global audit logger."""
        audit_logger = get_audit_logger()
        assert isinstance(audit_logger, AuditLogger)

    def test_correlation_context_decorator(self):
        """Test correlation context decorator."""
        logger = get_logger()
        initial_id = logger.get_correlation_id()

        @correlation_context("test_correlation")
        def test_function():
            return logger.get_correlation_id()

        result = test_function()
        assert result == "test_correlation"
        assert logger.get_correlation_id() == initial_id

    def test_log_performance_decorator(self):
        """Test log performance decorator."""
        logger = get_logger()

        with patch.object(logger, "log_performance") as mock_log:

            @log_performance("test_operation")
            def test_function():
                return "success"

            result = test_function()
            assert result == "success"
            mock_log.assert_called_once()

    def test_log_audit_event_decorator(self):
        """Test log audit event decorator."""
        audit_logger = get_audit_logger()

        with patch.object(audit_logger, "log_user_action") as mock_audit:

            @log_audit_event("test_action", "user123")
            def test_function():
                return "success"

            result = test_function()
            assert result == "success"
            mock_audit.assert_called_once()
            assert mock_audit.call_args[0][0] == "user123"
            assert mock_audit.call_args[0][1] == "test_action"
