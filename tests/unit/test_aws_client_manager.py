"""Tests for AWS client manager with circuit breaker and health checks."""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime

from ctrl_alt_heal.core.aws_client_manager import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    HealthCheckResult,
    AWSClientManager,
    get_aws_client_manager,
    get_aws_client,
    execute_aws_operation,
    health_check_aws_services,
    get_aws_service_status,
)
from ctrl_alt_heal.utils.exceptions import AWSServiceError


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in closed state."""
        config = CircuitBreakerConfig()
        cb = CircuitBreaker(config)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    def test_circuit_breaker_successful_call(self):
        """Test successful function call keeps circuit closed."""
        config = CircuitBreakerConfig()
        cb = CircuitBreaker(config)

        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_failure_opens_circuit(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(config)

        def failing_func():
            raise ValueError("Test error")

        # First failure
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1

        # Second failure opens circuit
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 2

    def test_circuit_breaker_recovery_timeout(self):
        """Test circuit transitions to half-open after recovery timeout."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1)
        cb = CircuitBreaker(config)

        def failing_func():
            raise ValueError("Test error")

        # Fail once to open circuit
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        # Should be able to call again (half-open)
        assert cb._can_execute() is True

    def test_circuit_breaker_success_after_failure(self):
        """Test circuit closes after successful call."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        cb = CircuitBreaker(config)

        def failing_func():
            raise ValueError("Test error")

        def success_func():
            return "success"

        # Fail twice to open circuit
        with pytest.raises(ValueError):
            cb.call(failing_func)
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        # Success should close circuit
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_get_status(self):
        """Test circuit breaker status reporting."""
        config = CircuitBreakerConfig()
        cb = CircuitBreaker(config)

        status = cb.get_status()
        assert status["state"] == CircuitState.CLOSED.value
        assert status["failure_count"] == 0
        assert status["last_failure_time"] is None


class TestAWSClientManager:
    """Test AWS client manager functionality."""

    @patch("boto3.Session")
    def test_aws_client_manager_initialization(self, mock_session):
        """Test AWS client manager initialization."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        manager = AWSClientManager("us-east-1")

        assert manager.region_name == "us-east-1"
        assert len(manager._circuit_breakers) > 0
        mock_session.assert_called_with(region_name="us-east-1")

    @patch("boto3.Session")
    def test_get_client(self, mock_session):
        """Test getting AWS client."""
        mock_session_instance = Mock()
        mock_client = Mock()
        mock_session_instance.client.return_value = mock_client
        mock_session.return_value = mock_session_instance

        manager = AWSClientManager()
        client = manager.get_client("s3")

        assert client == mock_client
        mock_session_instance.client.assert_called_with("s3")

    @patch("boto3.Session")
    def test_execute_with_circuit_breaker_success(self, mock_session):
        """Test successful execution with circuit breaker."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        manager = AWSClientManager()

        def test_operation():
            return "success"

        result = manager.execute_with_circuit_breaker(
            "s3", "test_operation", test_operation
        )
        assert result == "success"

    @patch("boto3.Session")
    def test_execute_with_circuit_breaker_failure(self, mock_session):
        """Test failed execution with circuit breaker."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        manager = AWSClientManager()

        def failing_operation():
            raise ValueError("Test error")

        with pytest.raises(AWSServiceError):
            manager.execute_with_circuit_breaker(
                "s3", "test_operation", failing_operation
            )

    @patch("boto3.Session")
    def test_health_check_s3_success(self, mock_session):
        """Test S3 health check success."""
        mock_session_instance = Mock()
        mock_client = Mock()
        mock_client.list_buckets.return_value = {"Buckets": []}
        mock_session_instance.client.return_value = mock_client
        mock_session.return_value = mock_session_instance

        manager = AWSClientManager()
        result = manager.health_check("s3")

        assert result.service == "s3"
        assert result.is_healthy is True
        assert result.response_time_ms > 0
        assert result.error_message is None

    @patch("boto3.Session")
    def test_health_check_s3_failure(self, mock_session):
        """Test S3 health check failure."""
        mock_session_instance = Mock()
        mock_client = Mock()
        mock_client.list_buckets.side_effect = Exception("S3 error")
        mock_session_instance.client.return_value = mock_client
        mock_session.return_value = mock_session_instance

        manager = AWSClientManager()
        result = manager.health_check("s3")

        assert result.service == "s3"
        assert result.is_healthy is False
        assert result.error_message == "S3 error"

    @patch("boto3.Session")
    def test_health_check_all_services(self, mock_session):
        """Test health check for all services."""
        mock_session_instance = Mock()
        mock_client = Mock()
        mock_client.list_buckets.return_value = {"Buckets": []}
        mock_client.list_tables.return_value = {"TableNames": []}
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_session_instance.client.return_value = mock_client
        mock_session.return_value = mock_session_instance

        manager = AWSClientManager()
        results = manager.health_check_all()

        assert len(results) > 0
        for service, result in results.items():
            assert isinstance(result, HealthCheckResult)
            assert result.service == service

    @patch("boto3.Session")
    def test_get_service_status(self, mock_session):
        """Test getting comprehensive service status."""
        mock_session_instance = Mock()
        mock_client = Mock()
        mock_client.list_buckets.return_value = {"Buckets": []}
        mock_session_instance.client.return_value = mock_client
        mock_session.return_value = mock_session_instance

        manager = AWSClientManager()
        status = manager.get_service_status()

        assert "region" in status
        assert "services" in status
        assert "overall_health" in status
        assert isinstance(status["overall_health"], bool)

    @patch("boto3.Session")
    def test_reset_circuit_breaker(self, mock_session):
        """Test resetting circuit breaker."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        manager = AWSClientManager()

        # Open a circuit breaker first
        def failing_operation():
            raise ValueError("Test error")

        for _ in range(3):  # failure_threshold
            try:
                manager.execute_with_circuit_breaker("s3", "test", failing_operation)
            except AWSServiceError:
                pass

        # Reset the circuit breaker
        manager.reset_circuit_breaker("s3")

        # Should be able to call again
        def success_operation():
            return "success"

        result = manager.execute_with_circuit_breaker("s3", "test", success_operation)
        assert result == "success"


class TestGlobalFunctions:
    """Test global AWS client manager functions."""

    @patch("ctrl_alt_heal.core.aws_client_manager.AWSClientManager")
    def test_get_aws_client_manager(self, mock_manager_class):
        """Test getting global AWS client manager."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        manager = get_aws_client_manager()
        assert manager == mock_manager

        # Second call should return same instance
        manager2 = get_aws_client_manager()
        assert manager2 == manager
        assert mock_manager_class.call_count == 1

    @patch("ctrl_alt_heal.core.aws_client_manager.get_aws_client_manager")
    def test_get_aws_client(self, mock_get_manager):
        """Test getting AWS client."""
        mock_manager = Mock()
        mock_client = Mock()
        mock_manager.get_client.return_value = mock_client
        mock_get_manager.return_value = mock_manager

        client = get_aws_client("s3")
        assert client == mock_client
        mock_manager.get_client.assert_called_with("s3")

    @patch("ctrl_alt_heal.core.aws_client_manager.get_aws_client_manager")
    def test_execute_aws_operation(self, mock_get_manager):
        """Test executing AWS operation."""
        mock_manager = Mock()
        mock_manager.execute_with_circuit_breaker.return_value = "success"
        mock_get_manager.return_value = mock_manager

        def test_operation():
            return "success"

        result = execute_aws_operation("s3", "test_operation", test_operation)
        assert result == "success"
        mock_manager.execute_with_circuit_breaker.assert_called_with(
            "s3", "test_operation", test_operation
        )

    @patch("ctrl_alt_heal.core.aws_client_manager.get_aws_client_manager")
    def test_health_check_aws_services(self, mock_get_manager):
        """Test health check for all AWS services."""
        mock_manager = Mock()
        mock_results = {"s3": Mock(), "dynamodb": Mock()}
        mock_manager.health_check_all.return_value = mock_results
        mock_get_manager.return_value = mock_manager

        results = health_check_aws_services()
        assert results == mock_results
        mock_manager.health_check_all.assert_called_once()

    @patch("ctrl_alt_heal.core.aws_client_manager.get_aws_client_manager")
    def test_get_aws_service_status(self, mock_get_manager):
        """Test getting AWS service status."""
        mock_manager = Mock()
        mock_status = {"overall_health": True, "services": {}}
        mock_manager.get_service_status.return_value = mock_status
        mock_get_manager.return_value = mock_manager

        status = get_aws_service_status()
        assert status == mock_status
        mock_manager.get_service_status.assert_called_once()


class TestHealthCheckResult:
    """Test health check result data class."""

    def test_health_check_result_creation(self):
        """Test creating health check result."""
        result = HealthCheckResult(
            service="s3", is_healthy=True, response_time_ms=100.5, error_message=None
        )

        assert result.service == "s3"
        assert result.is_healthy is True
        assert result.response_time_ms == 100.5
        assert result.error_message is None
        assert isinstance(result.timestamp, datetime)

    def test_health_check_result_with_error(self):
        """Test health check result with error."""
        result = HealthCheckResult(
            service="dynamodb",
            is_healthy=False,
            response_time_ms=500.0,
            error_message="Connection timeout",
        )

        assert result.service == "dynamodb"
        assert result.is_healthy is False
        assert result.response_time_ms == 500.0
        assert result.error_message == "Connection timeout"


class TestCircuitBreakerConfig:
    """Test circuit breaker configuration."""

    def test_circuit_breaker_config_defaults(self):
        """Test circuit breaker config defaults."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60
        assert config.expected_exception is Exception
        assert config.monitor_interval == 10

    def test_circuit_breaker_config_custom(self):
        """Test circuit breaker config with custom values."""
        config = CircuitBreakerConfig(
            failure_threshold=3, recovery_timeout=30, monitor_interval=5
        )

        assert config.failure_threshold == 3
        assert config.recovery_timeout == 30
        assert config.monitor_interval == 5
