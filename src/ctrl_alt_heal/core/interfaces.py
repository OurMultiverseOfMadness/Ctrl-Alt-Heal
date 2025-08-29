"""Service interfaces for Ctrl-Alt-Heal application."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ctrl_alt_heal.domain.models import User, ConversationHistory, Identity


class UserService(ABC):
    """Interface for user management operations."""

    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:
        """Update user data."""
        pass

    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        pass

    @abstractmethod
    def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List users with pagination."""
        pass


class PrescriptionService(ABC):
    """Interface for prescription management operations."""

    @abstractmethod
    def get_prescriptions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get prescriptions for a user."""
        pass

    @abstractmethod
    def create_prescription(
        self, user_id: str, prescription_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new prescription."""
        pass

    @abstractmethod
    def update_prescription(
        self, prescription_id: str, prescription_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a prescription."""
        pass

    @abstractmethod
    def delete_prescription(self, prescription_id: str) -> bool:
        """Delete a prescription."""
        pass

    @abstractmethod
    def extract_prescription_from_image(
        self, image_data: bytes, user_id: str
    ) -> Dict[str, Any]:
        """Extract prescription data from image."""
        pass


class MedicationScheduleService(ABC):
    """Interface for medication scheduling operations."""

    @abstractmethod
    def create_schedule(
        self, user_id: str, prescription_id: str, times: List[str], duration: int
    ) -> Dict[str, Any]:
        """Create a medication schedule."""
        pass

    @abstractmethod
    def update_schedule(
        self, user_id: str, prescription_id: str, times: List[str], duration: int
    ) -> Dict[str, Any]:
        """Update a medication schedule."""
        pass

    @abstractmethod
    def get_schedule(
        self, user_id: str, prescription_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a medication schedule."""
        pass

    @abstractmethod
    def delete_schedule(self, user_id: str, prescription_id: str) -> bool:
        """Delete a medication schedule."""
        pass

    @abstractmethod
    def get_all_schedules(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all schedules for a user."""
        pass

    @abstractmethod
    def generate_ics_file(
        self, user_id: str, prescription_id: Optional[str] = None
    ) -> bytes:
        """Generate ICS calendar file for medication reminders."""
        pass


class SessionService(ABC):
    """Interface for session management operations."""

    @abstractmethod
    def get_session(self, user_id: str) -> Optional[ConversationHistory]:
        """Get user's conversation session."""
        pass

    @abstractmethod
    def create_session(self, user_id: str) -> ConversationHistory:
        """Create a new conversation session."""
        pass

    @abstractmethod
    def update_session(
        self, user_id: str, message: str, role: str = "user"
    ) -> ConversationHistory:
        """Update session with new message."""
        pass

    @abstractmethod
    def clear_session(self, user_id: str) -> bool:
        """Clear user's conversation session."""
        pass

    @abstractmethod
    def is_session_expired(self, user_id: str, timeout_minutes: int = 30) -> bool:
        """Check if user's session has expired."""
        pass


class IdentityService(ABC):
    """Interface for identity management operations."""

    @abstractmethod
    def find_by_identity(
        self, identity_type: str, identity_value: str
    ) -> Optional[Identity]:
        """Find user by identity."""
        pass

    @abstractmethod
    def create_identity(
        self, user_id: str, identity_type: str, identity_value: str
    ) -> Identity:
        """Create a new identity."""
        pass

    @abstractmethod
    def get_or_create_user(
        self, identity_type: str, identity_value: str, user_data: Dict[str, Any]
    ) -> User:
        """Get existing user or create new one."""
        pass


class NotificationService(ABC):
    """Interface for notification operations."""

    @abstractmethod
    def send_message(self, chat_id: str, message: str) -> bool:
        """Send text message via Telegram."""
        pass

    @abstractmethod
    def send_file(
        self,
        chat_id: str,
        file_data: bytes,
        filename: str,
        caption: Optional[str] = None,
    ) -> bool:
        """Send file via Telegram."""
        pass

    @abstractmethod
    def send_medication_reminder(
        self, user_id: str, medication_name: str, time: str
    ) -> bool:
        """Send medication reminder notification."""
        pass


class AIService(ABC):
    """Interface for AI/ML operations."""

    @abstractmethod
    def process_message(self, message: str, context: Dict[str, Any]) -> str:
        """Process user message with AI."""
        pass

    @abstractmethod
    def extract_prescription_data(self, image_data: bytes) -> Dict[str, Any]:
        """Extract prescription data from image using AI."""
        pass

    @abstractmethod
    def describe_image(self, image_data: bytes) -> str:
        """Generate description of image using AI."""
        pass


class StorageService(ABC):
    """Interface for storage operations."""

    @abstractmethod
    def upload_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file to storage."""
        pass

    @abstractmethod
    def download_file(self, file_id: str) -> bytes:
        """Download file from storage."""
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    def get_file_url(self, file_id: str, expires_in: int = 3600) -> str:
        """Get presigned URL for file access."""
        pass


class ConfigurationService(ABC):
    """Interface for configuration management."""

    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting."""
        pass

    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """Set configuration setting."""
        pass

    @abstractmethod
    def get_secret(self, secret_name: str) -> str:
        """Get secret value."""
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate application configuration."""
        pass


class LoggingService(ABC):
    """Interface for logging operations."""

    @abstractmethod
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        pass

    @abstractmethod
    def log_warning(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    def log_error(
        self,
        message: str,
        error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log error message."""
        pass

    @abstractmethod
    def log_audit(
        self, action: str, user_id: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log audit event."""
        pass

    @abstractmethod
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log performance metric."""
        pass
