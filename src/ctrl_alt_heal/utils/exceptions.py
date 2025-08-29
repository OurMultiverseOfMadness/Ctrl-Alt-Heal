"""Custom exceptions for the Ctrl-Alt-Heal application."""

from __future__ import annotations

from typing import Any, Dict, Optional


class CtrlAltHealException(Exception):
    """Base exception for Ctrl-Alt-Heal application."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(CtrlAltHealException):
    """Raised when input validation fails."""

    def __init__(
        self, message: str, field: Optional[str] = None, value: Optional[Any] = None
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details)


class UserNotFoundError(CtrlAltHealException):
    """Raised when a user is not found."""

    def __init__(self, user_id: str):
        super().__init__(f"User not found: {user_id}", {"user_id": user_id})


class MedicationNotFoundError(CtrlAltHealException):
    """Raised when a medication is not found."""

    def __init__(self, medication_name: str, user_id: Optional[str] = None):
        details = {"medication_name": medication_name}
        if user_id:
            details["user_id"] = user_id
        super().__init__(f"Medication not found: {medication_name}", details)


class PrescriptionNotFoundError(CtrlAltHealException):
    """Raised when a prescription is not found."""

    def __init__(self, prescription_id: str, user_id: Optional[str] = None):
        details = {"prescription_id": prescription_id}
        if user_id:
            details["user_id"] = user_id
        super().__init__(f"Prescription not found: {prescription_id}", details)


class TimezoneError(CtrlAltHealException):
    """Raised when there's a timezone-related error."""

    def __init__(self, message: str, timezone: Optional[str] = None):
        details = {}
        if timezone:
            details["timezone"] = timezone
        super().__init__(message, details)


class TimeParsingError(CtrlAltHealException):
    """Raised when time parsing fails."""

    def __init__(self, message: str, time_input: Optional[str] = None):
        details = {}
        if time_input:
            details["time_input"] = time_input
        super().__init__(message, details)


class ScheduleError(CtrlAltHealException):
    """Raised when medication scheduling fails."""

    def __init__(
        self,
        message: str,
        medication_name: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        details = {}
        if medication_name:
            details["medication_name"] = medication_name
        if user_id:
            details["user_id"] = user_id
        super().__init__(message, details)


class FileProcessingError(CtrlAltHealException):
    """Raised when file processing fails."""

    def __init__(
        self,
        message: str,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
    ):
        details = {}
        if file_name:
            details["file_name"] = file_name
        if file_type:
            details["file_type"] = file_type
        super().__init__(message, details)


class AWSServiceError(CtrlAltHealException):
    """Raised when AWS service operations fail."""

    def __init__(
        self,
        message: str,
        service: str,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        details = {"service": service, "operation": operation, "error_code": error_code}
        super().__init__(message, details)


class TelegramAPIError(CtrlAltHealException):
    """Raised when Telegram API operations fail."""

    def __init__(
        self,
        message: str,
        chat_id: Optional[str] = None,
        error_code: Optional[int] = None,
    ):
        details = {}
        if chat_id:
            details["chat_id"] = chat_id
        if error_code:
            details["error_code"] = error_code
        super().__init__(message, details)


class BedrockError(CtrlAltHealException):
    """Raised when Amazon Bedrock operations fail."""

    def __init__(
        self,
        message: str,
        model_id: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        details = {}
        if model_id:
            details["model_id"] = model_id
        if error_code:
            details["error_code"] = error_code
        super().__init__(message, details)


class SessionError(CtrlAltHealException):
    """Raised when session management fails."""

    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if session_id:
            details["session_id"] = session_id
        super().__init__(message, details)


class ConfigurationError(CtrlAltHealException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details)


class DatabaseError(CtrlAltHealException):
    """Raised when database operations fail."""

    def __init__(
        self, message: str, table: Optional[str] = None, operation: Optional[str] = None
    ):
        details = {}
        if table:
            details["table"] = table
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class RateLimitError(CtrlAltHealException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str, service: str, retry_after: Optional[int] = None):
        details = {"service": service, "retry_after": retry_after}
        super().__init__(message, details)


class NetworkError(CtrlAltHealException):
    """Raised when network operations fail."""

    def __init__(
        self, message: str, url: Optional[str] = None, status_code: Optional[int] = None
    ):
        details = {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details)
