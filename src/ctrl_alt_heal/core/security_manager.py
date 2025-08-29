"""Security manager for enhanced input sanitization, rate limiting, and audit logging."""

from __future__ import annotations

import logging
import time
import re
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading


logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event information."""

    event_type: str
    severity: SecurityLevel
    user_id: Optional[str]
    ip_address: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    blocked: bool = False


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""

    name: str
    max_requests: int
    window_seconds: int
    action: str = "block"  # block, warn, log
    user_specific: bool = True


class InputSanitizer:
    """Enhanced input sanitization with multiple security levels."""

    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        self._init_patterns()

    def _init_patterns(self):
        """Initialize security patterns."""
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>",
            r"<form[^>]*>.*?</form>",
            r"<input[^>]*>",
            r"<textarea[^>]*>.*?</textarea>",
            r"<select[^>]*>.*?</select>",
            r"javascript:",
            r"vbscript:",
            r"data:",
            r"on\w+\s*=",
            r"expression\s*\(",
            r"url\s*\(",
        ]

        # SQL injection patterns
        self.sql_patterns = [
            r"\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b",
            r"\b(or|and)\b\s+\d+\s*=\s*\d+",
            r"(\bunion\b\s+\bselect\b)",
            r"(\binsert\b\s+\binto\b)",
            r"(\bupdate\b\s+\bset\b)",
            r"(\bdelete\b\s+\bfrom\b)",
            r"(\bdrop\b\s+\btable\b)",
            r"(\bcreate\b\s+\btable\b)",
            r"(\balter\b\s+\btable\b)",
            r"--\s*$",  # SQL comments
            r"/\*.*?\*/",  # SQL block comments
            r";\s*$",  # Multiple statements
        ]

        # Command injection patterns
        self.cmd_patterns = [
            r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ipconfig)\b",
            r"\b(rm|del|mkdir|touch|chmod|chown|chgrp)\b",
            r"\b(echo|printf|grep|sed|awk|cut|sort|uniq|head|tail)\b",
            r"\b(wget|curl|nc|telnet|ssh|scp|rsync)\b",
            r"\b(sudo|su|sudoers)\b",
            r"(\||&|;|`|$\(|\)|>|<)",  # Shell operators
        ]

        # Path traversal patterns
        self.path_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",  # URL encoded ../
            r"%2e%2e%5c",  # URL encoded ..\
            r"\.\.%2f",  # Mixed encoding
            r"\.\.%5c",  # Mixed encoding
        ]

        # NoSQL injection patterns
        self.nosql_patterns = [
            r"\$where\s*:",
            r"\$ne\s*:",
            r"\$gt\s*:",
            r"\$lt\s*:",
            r"\$regex\s*:",
            r"\$in\s*:",
            r"\$nin\s*:",
            r"\$exists\s*:",
        ]

    def sanitize(self, data: Any, context: str = "general") -> Any:
        """Sanitize input data based on security level."""
        if isinstance(data, str):
            return self._sanitize_string(data, context)
        elif isinstance(data, dict):
            return {key: self.sanitize(value, context) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize(item, context) for item in data]
        else:
            return data

    def _sanitize_string(self, value: str, context: str) -> str:
        """Sanitize a string value."""
        if not isinstance(value, str):
            return str(value)

        sanitized = value

        # Apply patterns based on security level
        if self.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            # Remove all potentially dangerous patterns
            for pattern in (
                self.xss_patterns
                + self.sql_patterns
                + self.cmd_patterns
                + self.path_patterns
                + self.nosql_patterns
            ):
                sanitized = re.sub(
                    pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL
                )

        elif self.security_level == SecurityLevel.MEDIUM:
            # Remove high-risk patterns
            for pattern in self.xss_patterns + self.sql_patterns + self.cmd_patterns:
                sanitized = re.sub(
                    pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL
                )

        else:  # LOW
            # Remove only critical patterns
            for pattern in (
                self.xss_patterns[:5] + self.sql_patterns[:3]
            ):  # Most critical patterns
                sanitized = re.sub(
                    pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL
                )

        # Context-specific sanitization
        if context == "sql":
            sanitized = self._sanitize_for_sql(sanitized)
        elif context == "html":
            sanitized = self._sanitize_for_html(sanitized)
        elif context == "url":
            sanitized = self._sanitize_for_url(sanitized)
        elif context == "filename":
            sanitized = self._sanitize_for_filename(sanitized)

        # Remove control characters
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", sanitized)

        # Normalize whitespace
        sanitized = re.sub(r"\s+", " ", sanitized)
        sanitized = sanitized.strip()

        return sanitized

    def _sanitize_for_sql(self, value: str) -> str:
        """Additional sanitization for SQL context."""
        # Remove SQL-specific patterns
        sql_escapes = ["'", '"', ";", "--", "/*", "*/"]
        for escape in sql_escapes:
            value = value.replace(escape, "")
        return value

    def _sanitize_for_html(self, value: str) -> str:
        """Additional sanitization for HTML context."""
        # HTML entity encoding for critical characters
        html_entities = {
            "<": "&lt;",
            ">": "&gt;",
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#39;",
        }
        for char, entity in html_entities.items():
            value = value.replace(char, entity)
        return value

    def _sanitize_for_url(self, value: str) -> str:
        """Additional sanitization for URL context."""
        # Remove URL-specific dangerous patterns
        url_dangerous = ["javascript:", "vbscript:", "data:", "file:"]
        for pattern in url_dangerous:
            value = value.replace(pattern.lower(), "")
        return value

    def _sanitize_for_filename(self, value: str) -> str:
        """Additional sanitization for filename context."""
        # Remove filename-specific dangerous characters
        filename_dangerous = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        for char in filename_dangerous:
            value = value.replace(char, "_")
        return value

    def validate_input(
        self, data: Any, rules: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate input against security rules."""
        errors = []

        if isinstance(data, str):
            # Length validation
            if "max_length" in rules and len(data) > rules["max_length"]:
                errors.append(f"Input too long (max {rules['max_length']} characters)")

            if "min_length" in rules and len(data) < rules["min_length"]:
                errors.append(f"Input too short (min {rules['min_length']} characters)")

            # Pattern validation
            if "pattern" in rules and not re.match(rules["pattern"], data):
                errors.append("Input doesn't match required pattern")

            # Content validation
            if "forbidden_patterns" in rules:
                for pattern in rules["forbidden_patterns"]:
                    if re.search(pattern, data, re.IGNORECASE):
                        errors.append("Input contains forbidden content")
                        break

        return len(errors) == 0, errors


class RateLimiter:
    """Rate limiting implementation."""

    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
        self._rules: Dict[str, RateLimitRule] = {}
        self._blocked_ips: Set[str] = set()
        self._lock = threading.RLock()

        # Register default rules
        self._register_default_rules()

    def _register_default_rules(self):
        """Register default rate limiting rules."""
        self.add_rule(
            RateLimitRule(name="general", max_requests=100, window_seconds=60)
        )

        self.add_rule(RateLimitRule(name="api", max_requests=50, window_seconds=60))

        self.add_rule(
            RateLimitRule(
                name="login",
                max_requests=5,
                window_seconds=300,  # 5 minutes
            )
        )

    def add_rule(self, rule: RateLimitRule):
        """Add a rate limiting rule."""
        with self._lock:
            self._rules[rule.name] = rule

    def check_rate_limit(
        self, identifier: str, rule_name: str = "general"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits."""
        with self._lock:
            rule = self._rules.get(rule_name)
            if not rule:
                return True, {"allowed": True, "rule": "default"}

            now = time.time()
            key = f"{identifier}:{rule_name}"

            # Clean old requests
            if key in self._requests:
                self._requests[key] = [
                    req_time
                    for req_time in self._requests[key]
                    if now - req_time < rule.window_seconds
                ]
            else:
                self._requests[key] = []

            # Check if limit exceeded
            if len(self._requests[key]) >= rule.max_requests:
                return False, {
                    "allowed": False,
                    "rule": rule_name,
                    "limit": rule.max_requests,
                    "window": rule.window_seconds,
                    "remaining_time": rule.window_seconds
                    - (now - self._requests[key][0]),
                }

            # Add current request
            self._requests[key].append(now)

            return True, {
                "allowed": True,
                "rule": rule_name,
                "limit": rule.max_requests,
                "remaining": rule.max_requests - len(self._requests[key]),
                "window": rule.window_seconds,
            }

    def block_ip(self, ip_address: str, duration_seconds: int = 3600):
        """Block an IP address temporarily."""
        with self._lock:
            self._blocked_ips.add(ip_address)
            # Schedule unblock
            threading.Timer(
                duration_seconds, self._unblock_ip, args=[ip_address]
            ).start()

    def _unblock_ip(self, ip_address: str):
        """Unblock an IP address."""
        with self._lock:
            self._blocked_ips.discard(ip_address)

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked."""
        with self._lock:
            return ip_address in self._blocked_ips


class SecurityManager:
    """Main security manager."""

    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        self.sanitizer = InputSanitizer(security_level)
        self.rate_limiter = RateLimiter()
        self._security_events: List[SecurityEvent] = []
        self._lock = threading.RLock()
        self._max_events = 10000

        # Security monitoring
        self._suspicious_patterns: Set[str] = set()
        self._failed_attempts: Dict[str, int] = {}

        # Initialize security monitoring
        self._init_security_monitoring()

    def _init_security_monitoring(self):
        """Initialize security monitoring patterns."""
        # Common attack patterns
        self._suspicious_patterns.update(
            [
                "admin",
                "root",
                "test",
                "debug",
                "password",
                "secret",
                "union select",
                "drop table",
                "exec",
                "javascript:",
                "../",
                "..\\",
                "script",
                "iframe",
                "onload",
            ]
        )

    def sanitize_input(self, data: Any, context: str = "general") -> Any:
        """Sanitize input data."""
        return self.sanitizer.sanitize(data, context)

    def validate_input(
        self, data: Any, rules: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate input against security rules."""
        return self.sanitizer.validate_input(data, rules)

    def check_rate_limit(
        self, identifier: str, rule_name: str = "general"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limits."""
        return self.rate_limiter.check_rate_limit(identifier, rule_name)

    def record_security_event(
        self,
        event_type: str,
        severity: SecurityLevel,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        blocked: bool = False,
    ) -> SecurityEvent:
        """Record a security event."""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            details=details or {},
            blocked=blocked,
        )

        with self._lock:
            self._security_events.append(event)

            # Trim old events
            if len(self._security_events) > self._max_events:
                self._security_events = self._security_events[-self._max_events :]

        # Log security event
        logger.warning(
            f"Security event: {event_type} - {severity.value} - User: {user_id} - IP: {ip_address}"
        )

        return event

    def detect_suspicious_activity(
        self, data: str, user_id: Optional[str] = None, ip_address: Optional[str] = None
    ) -> List[str]:
        """Detect suspicious activity in input data."""
        suspicious_activities = []

        # Check for suspicious patterns
        data_lower = data.lower()
        for pattern in self._suspicious_patterns:
            if pattern in data_lower:
                suspicious_activities.append(f"Suspicious pattern detected: {pattern}")

        # Check for repeated failed attempts
        if user_id:
            failed_count = self._failed_attempts.get(user_id, 0)
            if failed_count > 5:
                suspicious_activities.append(
                    f"Multiple failed attempts: {failed_count}"
                )

        # Record suspicious activity
        if suspicious_activities:
            self.record_security_event(
                event_type="suspicious_activity",
                severity=SecurityLevel.MEDIUM,
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "activities": suspicious_activities,
                    "data_preview": data[:100],
                },
            )

        return suspicious_activities

    def increment_failed_attempts(self, identifier: str):
        """Increment failed attempts counter."""
        with self._lock:
            self._failed_attempts[identifier] = (
                self._failed_attempts.get(identifier, 0) + 1
            )

    def reset_failed_attempts(self, identifier: str):
        """Reset failed attempts counter."""
        with self._lock:
            self._failed_attempts.pop(identifier, None)

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary."""
        with self._lock:
            recent_events = [
                event
                for event in self._security_events
                if event.timestamp > datetime.now() - timedelta(hours=24)
            ]

            # Count events by severity
            severity_counts = {}
            for severity in SecurityLevel:
                severity_counts[severity.value] = len(
                    [event for event in recent_events if event.severity == severity]
                )

            # Count blocked events
            blocked_count = len([event for event in recent_events if event.blocked])

            return {
                "security_level": self.security_level.value,
                "recent_events": len(recent_events),
                "severity_counts": severity_counts,
                "blocked_events": blocked_count,
                "failed_attempts": len(self._failed_attempts),
                "blocked_ips": len(self.rate_limiter._blocked_ips),
                "timestamp": datetime.now().isoformat(),
            }

    def get_recent_events(self, hours: int = 24) -> List[SecurityEvent]:
        """Get recent security events."""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._lock:
            return [
                event for event in self._security_events if event.timestamp > cutoff
            ]

    def generate_audit_log(
        self, user_id: str, action: str, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate audit log entry."""
        audit_entry = {
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "security_level": self.security_level.value,
        }

        # Log audit entry
        logger.info(f"Audit: {action} by {user_id}")

        return audit_entry


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager(
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
) -> SecurityManager:
    """Get the global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager(security_level)
    return _security_manager


def sanitize_input(data: Any, context: str = "general") -> Any:
    """Sanitize input data."""
    manager = get_security_manager()
    return manager.sanitize_input(data, context)


def validate_input(data: Any, rules: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate input against security rules."""
    manager = get_security_manager()
    return manager.validate_input(data, rules)


def check_rate_limit(
    identifier: str, rule_name: str = "general"
) -> Tuple[bool, Dict[str, Any]]:
    """Check rate limits."""
    manager = get_security_manager()
    return manager.check_rate_limit(identifier, rule_name)


def record_security_event(
    event_type: str,
    severity: SecurityLevel,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    blocked: bool = False,
) -> SecurityEvent:
    """Record a security event."""
    manager = get_security_manager()
    return manager.record_security_event(
        event_type, severity, user_id, ip_address, details, blocked
    )


def get_security_summary() -> Dict[str, Any]:
    """Get security summary."""
    manager = get_security_manager()
    return manager.get_security_summary()
