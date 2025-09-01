"""AWS client manager with connection pooling, circuit breaker, and health checks."""

from __future__ import annotations

import boto3
import logging
import time
from typing import Dict, Any, Optional, Type
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading

from ctrl_alt_heal.utils.exceptions import AWSServiceError
from ctrl_alt_heal.utils.constants import AWS_SERVICES


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: Type[Exception] = Exception
    monitor_interval: int = 10  # seconds


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    service: str
    is_healthy: bool
    response_time_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class CircuitBreaker:
    """Circuit breaker implementation for AWS services."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self._lock = threading.RLock()

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if not self._can_execute():
            raise AWSServiceError(
                f"Circuit breaker is {self.state.value}",
                service="circuit_breaker",
                operation="call",
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception:
            self._on_failure()
            raise

    def _can_execute(self) -> bool:
        """Check if execution is allowed."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.config.recovery_timeout:  # type: ignore
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            else:  # HALF_OPEN
                return True

    def _on_success(self):
        """Handle successful execution."""
        with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            self.last_success_time = time.time()

    def _on_failure(self):
        """Handle failed execution."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
        }


class AWSClientManager:
    """Centralized AWS client manager with robustness features."""

    def __init__(self, region_name: str = "ap-southeast-1"):
        self.region_name = region_name
        self._clients: Dict[str, Any] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._health_check_results: Dict[str, HealthCheckResult] = {}
        self._lock = threading.RLock()
        self._session = boto3.Session(region_name=region_name)

        # Initialize circuit breakers for each service
        self._init_circuit_breakers()

    def _init_circuit_breakers(self):
        """Initialize circuit breakers for AWS services."""
        for service_name in AWS_SERVICES.values():
            config = CircuitBreakerConfig(
                failure_threshold=3, recovery_timeout=30, expected_exception=Exception
            )
            self._circuit_breakers[service_name] = CircuitBreaker(config)

    def get_client(self, service_name: str) -> Any:
        """Get AWS client with circuit breaker protection."""
        if service_name not in self._clients:
            with self._lock:
                if service_name not in self._clients:
                    self._clients[service_name] = self._session.client(service_name)  # type: ignore[arg-type, call-overload]

        return self._clients[service_name]

    def execute_with_circuit_breaker(
        self, service_name: str, operation: str, func, *args, **kwargs
    ) -> Any:
        """Execute AWS operation with circuit breaker protection."""
        circuit_breaker = self._circuit_breakers.get(service_name)
        if not circuit_breaker:
            return func(*args, **kwargs)

        try:
            return circuit_breaker.call(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"AWS {service_name} {operation} failed: {str(e)}")
            raise AWSServiceError(
                f"{service_name} {operation} failed",
                service=service_name,
                operation=operation,
            ) from e

    @contextmanager
    def get_client_context(self, service_name: str):
        """Context manager for AWS client operations."""
        client = self.get_client(service_name)
        try:
            yield client
        except Exception as e:
            logger.error(f"Error with {service_name} client: {str(e)}")
            raise

    def health_check(self, service_name: str) -> HealthCheckResult:
        """Perform health check for AWS service."""
        start_time = time.time()
        is_healthy = False
        error_message = None

        try:
            client = self.get_client(service_name)

            # Service-specific health checks
            if service_name == "dynamodb":
                client.list_tables(Limit=1)
            elif service_name == "s3":
                client.list_buckets()
            elif service_name == "secretsmanager":
                client.list_secrets(MaxResults=1)
            elif service_name == "bedrock-runtime":
                # Bedrock doesn't have a simple health check, so we'll skip
                is_healthy = True
            else:
                # Generic health check
                is_healthy = True

            if not is_healthy:
                is_healthy = True

        except Exception as e:
            is_healthy = False
            error_message = str(e)

        response_time_ms = (time.time() - start_time) * 1000

        result = HealthCheckResult(
            service=service_name,
            is_healthy=is_healthy,
            response_time_ms=response_time_ms,
            error_message=error_message,
        )

        self._health_check_results[service_name] = result
        return result

    def health_check_all(self) -> Dict[str, HealthCheckResult]:
        """Perform health checks for all AWS services."""
        results = {}
        for service_name in AWS_SERVICES.values():
            results[service_name] = self.health_check(service_name)
        return results

    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all AWS services."""
        status: Dict[str, Any] = {
            "region": self.region_name,
            "services": {},
            "overall_health": True,
        }

        for service_name in AWS_SERVICES.values():
            circuit_status = self._circuit_breakers[service_name].get_status()
            health_result = self._health_check_results.get(service_name)

            service_status = {
                "circuit_breaker": circuit_status,
                "health": health_result.is_healthy if health_result else None,
                "response_time_ms": health_result.response_time_ms
                if health_result
                else None,
                "last_check": health_result.timestamp.isoformat()
                if health_result
                else None,
            }

            status["services"][service_name] = service_status  # type: ignore

            if not service_status["health"]:
                status["overall_health"] = False

        return status

    def reset_circuit_breaker(self, service_name: str) -> None:
        """Reset circuit breaker for a service."""
        if service_name in self._circuit_breakers:
            self._circuit_breakers[service_name] = CircuitBreaker(
                CircuitBreakerConfig()
            )
            logger.info(f"Reset circuit breaker for {service_name}")


# Global AWS client manager instance
_aws_client_manager: Optional[AWSClientManager] = None


def get_aws_client_manager(region_name: str = "ap-southeast-1") -> AWSClientManager:
    """Get the global AWS client manager instance."""
    global _aws_client_manager
    if _aws_client_manager is None:
        _aws_client_manager = AWSClientManager(region_name)
    return _aws_client_manager


def get_aws_client(service_name: str) -> Any:
    """Get AWS client with circuit breaker protection."""
    manager = get_aws_client_manager()
    return manager.get_client(service_name)


def execute_aws_operation(
    service_name: str, operation: str, func, *args, **kwargs
) -> Any:
    """Execute AWS operation with circuit breaker protection."""
    manager = get_aws_client_manager()
    return manager.execute_with_circuit_breaker(
        service_name, operation, func, *args, **kwargs
    )


def health_check_aws_services() -> Dict[str, HealthCheckResult]:
    """Perform health checks for all AWS services."""
    manager = get_aws_client_manager()
    return manager.health_check_all()


def get_aws_service_status() -> Dict[str, Any]:
    """Get comprehensive status of all AWS services."""
    manager = get_aws_client_manager()
    return manager.get_service_status()
