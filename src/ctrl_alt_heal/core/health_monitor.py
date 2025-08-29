"""Health monitoring and metrics collection system."""

from __future__ import annotations

import logging
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ctrl_alt_heal.core.aws_client_manager import get_aws_service_status


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Health metric data."""

    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check result."""

    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert information."""

    id: str
    severity: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False


class MetricsCollector:
    """Collects and stores application metrics."""

    def __init__(self):
        self._metrics: List[HealthMetric] = []
        self._lock = threading.RLock()
        self._max_metrics = 10000  # Keep last 10k metrics

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ):
        """Record a metric."""
        with self._lock:
            metric = HealthMetric(name=name, value=value, unit=unit, tags=tags or {})
            self._metrics.append(metric)

            # Trim old metrics if we exceed the limit
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics :]

    def get_metrics(
        self, name: Optional[str] = None, since: Optional[datetime] = None
    ) -> List[HealthMetric]:
        """Get metrics with optional filtering."""
        with self._lock:
            metrics = self._metrics

            if name:
                metrics = [m for m in metrics if m.name == name]

            if since:
                metrics = [m for m in metrics if m.timestamp >= since]

            return metrics

    def get_latest_metric(self, name: str) -> Optional[HealthMetric]:
        """Get the latest metric for a given name."""
        metrics = self.get_metrics(name)
        return metrics[-1] if metrics else None

    def get_metric_summary(self, name: str, window_minutes: int = 60) -> Dict[str, Any]:
        """Get metric summary for a time window."""
        since = datetime.now() - timedelta(minutes=window_minutes)
        metrics = self.get_metrics(name, since)

        if not metrics:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}

        values = [m.value for m in metrics]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1],
        }


class HealthMonitor:
    """Main health monitoring system."""

    def __init__(self):
        self._health_checks: Dict[str, Callable] = {}
        self._alerts: List[Alert] = []
        self._metrics_collector = MetricsCollector()
        self._lock = threading.RLock()
        self._monitoring_enabled = True

        # Register default health checks
        self._register_default_health_checks()

    def _register_default_health_checks(self):
        """Register default health checks."""
        self.register_health_check("aws_services", self._check_aws_services)
        self.register_health_check("application_health", self._check_application_health)
        self.register_health_check("memory_usage", self._check_memory_usage)
        self.register_health_check("response_times", self._check_response_times)

    def register_health_check(self, name: str, check_func: Callable[[], HealthCheck]):
        """Register a health check function."""
        with self._lock:
            self._health_checks[name] = check_func

    def run_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        if not self._monitoring_enabled:
            return {}

        results = {}
        for name, check_func in self._health_checks.items():
            try:
                start_time = time.time()
                result = check_func()
                response_time = (time.time() - start_time) * 1000

                # Update response time if not set
                if result.response_time_ms == 0:
                    result.response_time_ms = response_time

                results[name] = result

                # Record metrics
                self._metrics_collector.record_metric(
                    f"health_check.{name}.response_time", result.response_time_ms, "ms"
                )

                self._metrics_collector.record_metric(
                    f"health_check.{name}.status",
                    1 if result.status == HealthStatus.HEALTHY else 0,
                )

                # Check for alerts
                self._check_for_alerts(name, result)

            except Exception as e:
                logger.error(f"Health check {name} failed: {str(e)}")
                result = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                    response_time_ms=0,
                )
                results[name] = result

        return results

    def _check_aws_services(self) -> HealthCheck:
        """Check AWS services health."""
        try:
            aws_status = get_aws_service_status()

            if aws_status["overall_health"]:
                return HealthCheck(
                    name="aws_services",
                    status=HealthStatus.HEALTHY,
                    message="All AWS services are healthy",
                    response_time_ms=0,
                )
            else:
                unhealthy_services = [
                    service
                    for service, status in aws_status["services"].items()
                    if not status["health"]
                ]
                return HealthCheck(
                    name="aws_services",
                    status=HealthStatus.DEGRADED,
                    message=f"Unhealthy services: {', '.join(unhealthy_services)}",
                    response_time_ms=0,
                    details=aws_status,
                )
        except Exception as e:
            return HealthCheck(
                name="aws_services",
                status=HealthStatus.UNHEALTHY,
                message=f"AWS services check failed: {str(e)}",
                response_time_ms=0,
            )

    def _check_application_health(self) -> HealthCheck:
        """Check application health."""
        try:
            # Basic application health check
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Record metrics
            self._metrics_collector.record_metric(
                "system.cpu_percent", cpu_percent, "%"
            )
            self._metrics_collector.record_metric(
                "system.memory_percent", memory.percent, "%"
            )

            if cpu_percent > 90 or memory.percent > 90:
                return HealthCheck(
                    name="application_health",
                    status=HealthStatus.DEGRADED,
                    message=f"High resource usage: CPU {cpu_percent}%, Memory {memory.percent}%",
                    response_time_ms=0,
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                    },
                )
            else:
                return HealthCheck(
                    name="application_health",
                    status=HealthStatus.HEALTHY,
                    message=f"Application healthy: CPU {cpu_percent}%, Memory {memory.percent}%",
                    response_time_ms=0,
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                    },
                )
        except ImportError:
            # psutil not available, skip this check
            return HealthCheck(
                name="application_health",
                status=HealthStatus.UNKNOWN,
                message="psutil not available for system monitoring",
                response_time_ms=0,
            )
        except Exception as e:
            return HealthCheck(
                name="application_health",
                status=HealthStatus.UNHEALTHY,
                message=f"Application health check failed: {str(e)}",
                response_time_ms=0,
            )

    def _check_memory_usage(self) -> HealthCheck:
        """Check memory usage."""
        try:
            import psutil

            memory = psutil.virtual_memory()

            self._metrics_collector.record_metric(
                "system.memory_used", memory.used, "bytes"
            )
            self._metrics_collector.record_metric(
                "system.memory_available", memory.available, "bytes"
            )

            if memory.percent > 95:
                return HealthCheck(
                    name="memory_usage",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Critical memory usage: {memory.percent}%",
                    response_time_ms=0,
                    details={"memory_percent": memory.percent},
                )
            elif memory.percent > 80:
                return HealthCheck(
                    name="memory_usage",
                    status=HealthStatus.DEGRADED,
                    message=f"High memory usage: {memory.percent}%",
                    response_time_ms=0,
                    details={"memory_percent": memory.percent},
                )
            else:
                return HealthCheck(
                    name="memory_usage",
                    status=HealthStatus.HEALTHY,
                    message=f"Memory usage normal: {memory.percent}%",
                    response_time_ms=0,
                    details={"memory_percent": memory.percent},
                )
        except ImportError:
            return HealthCheck(
                name="memory_usage",
                status=HealthStatus.UNKNOWN,
                message="psutil not available for memory monitoring",
                response_time_ms=0,
            )
        except Exception as e:
            return HealthCheck(
                name="memory_usage",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}",
                response_time_ms=0,
            )

    def _check_response_times(self) -> HealthCheck:
        """Check response times."""
        try:
            # Get recent response time metrics
            recent_metrics = self._metrics_collector.get_metrics(
                since=datetime.now() - timedelta(minutes=5)
            )

            response_time_metrics = [
                m for m in recent_metrics if "response_time" in m.name
            ]

            if not response_time_metrics:
                return HealthCheck(
                    name="response_times",
                    status=HealthStatus.UNKNOWN,
                    message="No response time data available",
                    response_time_ms=0,
                )

            avg_response_time = sum(m.value for m in response_time_metrics) / len(
                response_time_metrics
            )

            self._metrics_collector.record_metric(
                "system.avg_response_time", avg_response_time, "ms"
            )

            if avg_response_time > 5000:  # 5 seconds
                return HealthCheck(
                    name="response_times",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Very slow response times: {avg_response_time:.1f}ms average",
                    response_time_ms=0,
                    details={"avg_response_time_ms": avg_response_time},
                )
            elif avg_response_time > 2000:  # 2 seconds
                return HealthCheck(
                    name="response_times",
                    status=HealthStatus.DEGRADED,
                    message=f"Slow response times: {avg_response_time:.1f}ms average",
                    response_time_ms=0,
                    details={"avg_response_time_ms": avg_response_time},
                )
            else:
                return HealthCheck(
                    name="response_times",
                    status=HealthStatus.HEALTHY,
                    message=f"Response times normal: {avg_response_time:.1f}ms average",
                    response_time_ms=0,
                    details={"avg_response_time_ms": avg_response_time},
                )
        except Exception as e:
            return HealthCheck(
                name="response_times",
                status=HealthStatus.UNHEALTHY,
                message=f"Response time check failed: {str(e)}",
                response_time_ms=0,
            )

    def _check_for_alerts(self, check_name: str, result: HealthCheck):
        """Check if health check result should trigger an alert."""
        if result.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
            alert_id = f"{check_name}_{result.timestamp.strftime('%Y%m%d_%H%M%S')}"

            # Check if alert already exists
            existing_alert = next((a for a in self._alerts if a.id == alert_id), None)

            if not existing_alert:
                severity = (
                    "critical" if result.status == HealthStatus.UNHEALTHY else "warning"
                )
                alert = Alert(
                    id=alert_id,
                    severity=severity,
                    message=f"{check_name}: {result.message}",
                )

                with self._lock:
                    self._alerts.append(alert)

                logger.warning(f"Health alert: {alert.message}")

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        health_checks = self.run_health_checks()

        # Count statuses
        status_counts = {}
        for status in HealthStatus:
            status_counts[status.value] = len(
                [check for check in health_checks.values() if check.status == status]
            )

        # Determine overall status
        if status_counts.get("unhealthy", 0) > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif status_counts.get("degraded", 0) > 0:
            overall_status = HealthStatus.DEGRADED
        elif status_counts.get("healthy", 0) > 0:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN

        return {
            "overall_status": overall_status.value,
            "status_counts": status_counts,
            "health_checks": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "timestamp": check.timestamp.isoformat(),
                }
                for name, check in health_checks.items()
            },
            "metrics_summary": {
                "total_metrics": len(self._metrics_collector._metrics),
                "recent_alerts": len([a for a in self._alerts if not a.resolved]),
            },
            "timestamp": datetime.now().isoformat(),
        }

    def get_alerts(self, unresolved_only: bool = True) -> List[Alert]:
        """Get alerts."""
        with self._lock:
            if unresolved_only:
                return [a for a in self._alerts if not a.resolved]
            return self._alerts.copy()

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    return True
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    return True
            return False

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ):
        """Record a metric."""
        self._metrics_collector.record_metric(name, value, unit, tags)

    def get_metrics(
        self, name: Optional[str] = None, since: Optional[datetime] = None
    ) -> List[HealthMetric]:
        """Get metrics."""
        return self._metrics_collector.get_metrics(name, since)

    def get_metric_summary(self, name: str, window_minutes: int = 60) -> Dict[str, Any]:
        """Get metric summary."""
        return self._metrics_collector.get_metric_summary(name, window_minutes)


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


def health_check() -> Dict[str, Any]:
    """Perform health check and return summary."""
    monitor = get_health_monitor()
    return monitor.get_health_summary()


def record_metric(
    name: str, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None
):
    """Record a metric."""
    monitor = get_health_monitor()
    monitor.record_metric(name, value, unit, tags)


def get_metrics(
    name: Optional[str] = None, since: Optional[datetime] = None
) -> List[HealthMetric]:
    """Get metrics."""
    monitor = get_health_monitor()
    return monitor.get_metrics(name, since)
