"""Tests for custom exceptions."""

from ctrl_alt_heal.utils.exceptions import (
    CtrlAltHealException,
    ValidationError,
    UserNotFoundError,
    MedicationNotFoundError,
    PrescriptionNotFoundError,
    TimezoneError,
    TimeParsingError,
    ScheduleError,
    FileProcessingError,
    AWSServiceError,
    TelegramAPIError,
    BedrockError,
    SessionError,
    ConfigurationError,
    DatabaseError,
    RateLimitError,
    NetworkError,
)


class TestCtrlAltHealException:
    """Test base exception class."""

    def test_base_exception_creation(self):
        """Test creating base exception."""
        exc = CtrlAltHealException("Test message")
        assert str(exc) == "Test message"
        assert exc.message == "Test message"
        assert exc.details == {}

    def test_base_exception_with_details(self):
        """Test creating base exception with details."""
        details = {"field": "test", "value": 123}
        exc = CtrlAltHealException("Test message", details)
        assert exc.message == "Test message"
        assert exc.details == details

    def test_to_dict_method(self):
        """Test converting exception to dictionary."""
        details = {"field": "test"}
        exc = CtrlAltHealException("Test message", details)
        result = exc.to_dict()

        assert result["error_type"] == "CtrlAltHealException"
        assert result["message"] == "Test message"
        assert result["details"] == details


class TestValidationError:
    """Test validation error."""

    def test_validation_error_creation(self):
        """Test creating validation error."""
        exc = ValidationError("Invalid input", "user_id", "invalid_value")
        assert exc.message == "Invalid input"
        assert exc.details["field"] == "user_id"
        assert exc.details["value"] == "invalid_value"

    def test_validation_error_without_field(self):
        """Test creating validation error without field."""
        exc = ValidationError("Invalid input")
        assert exc.message == "Invalid input"
        assert "field" not in exc.details


class TestUserNotFoundError:
    """Test user not found error."""

    def test_user_not_found_error(self):
        """Test creating user not found error."""
        exc = UserNotFoundError("user123")
        assert "user123" in exc.message
        assert exc.details["user_id"] == "user123"


class TestMedicationNotFoundError:
    """Test medication not found error."""

    def test_medication_not_found_error(self):
        """Test creating medication not found error."""
        exc = MedicationNotFoundError("Aspirin", "user123")
        assert "Aspirin" in exc.message
        assert exc.details["medication_name"] == "Aspirin"
        assert exc.details["user_id"] == "user123"

    def test_medication_not_found_error_without_user(self):
        """Test creating medication not found error without user."""
        exc = MedicationNotFoundError("Aspirin")
        assert "Aspirin" in exc.message
        assert exc.details["medication_name"] == "Aspirin"
        assert "user_id" not in exc.details


class TestPrescriptionNotFoundError:
    """Test prescription not found error."""

    def test_prescription_not_found_error(self):
        """Test creating prescription not found error."""
        exc = PrescriptionNotFoundError("prescription123", "user123")
        assert "prescription123" in exc.message
        assert exc.details["prescription_id"] == "prescription123"
        assert exc.details["user_id"] == "user123"


class TestTimezoneError:
    """Test timezone error."""

    def test_timezone_error(self):
        """Test creating timezone error."""
        exc = TimezoneError("Invalid timezone", "EST")
        assert exc.message == "Invalid timezone"
        assert exc.details["timezone"] == "EST"


class TestTimeParsingError:
    """Test time parsing error."""

    def test_time_parsing_error(self):
        """Test creating time parsing error."""
        exc = TimeParsingError("Invalid time format", "25:00")
        assert exc.message == "Invalid time format"
        assert exc.details["time_input"] == "25:00"


class TestScheduleError:
    """Test schedule error."""

    def test_schedule_error(self):
        """Test creating schedule error."""
        exc = ScheduleError("Schedule creation failed", "Aspirin", "user123")
        assert exc.message == "Schedule creation failed"
        assert exc.details["medication_name"] == "Aspirin"
        assert exc.details["user_id"] == "user123"


class TestFileProcessingError:
    """Test file processing error."""

    def test_file_processing_error(self):
        """Test creating file processing error."""
        exc = FileProcessingError("File upload failed", "test.jpg", "image")
        assert exc.message == "File upload failed"
        assert exc.details["file_name"] == "test.jpg"
        assert exc.details["file_type"] == "image"


class TestAWSServiceError:
    """Test AWS service error."""

    def test_aws_service_error(self):
        """Test creating AWS service error."""
        exc = AWSServiceError("S3 operation failed", "s3", "put_object", "AccessDenied")
        assert exc.message == "S3 operation failed"
        assert exc.details["service"] == "s3"
        assert exc.details["operation"] == "put_object"
        assert exc.details["error_code"] == "AccessDenied"


class TestTelegramAPIError:
    """Test Telegram API error."""

    def test_telegram_api_error(self):
        """Test creating Telegram API error."""
        exc = TelegramAPIError("Message send failed", "chat123", 400)
        assert exc.message == "Message send failed"
        assert exc.details["chat_id"] == "chat123"
        assert exc.details["error_code"] == "400"


class TestBedrockError:
    """Test Bedrock error."""

    def test_bedrock_error(self):
        """Test creating Bedrock error."""
        exc = BedrockError("Model invocation failed", "nova-1", "ModelNotFound")
        assert exc.message == "Model invocation failed"
        assert exc.details["model_id"] == "nova-1"
        assert exc.details["error_code"] == "ModelNotFound"


class TestSessionError:
    """Test session error."""

    def test_session_error(self):
        """Test creating session error."""
        exc = SessionError("Session creation failed", "user123", "session456")
        assert exc.message == "Session creation failed"
        assert exc.details["user_id"] == "user123"
        assert exc.details["session_id"] == "session456"


class TestConfigurationError:
    """Test configuration error."""

    def test_configuration_error(self):
        """Test creating configuration error."""
        exc = ConfigurationError("Missing configuration", "API_KEY")
        assert exc.message == "Missing configuration"
        assert exc.details["config_key"] == "API_KEY"


class TestDatabaseError:
    """Test database error."""

    def test_database_error(self):
        """Test creating database error."""
        exc = DatabaseError("Query failed", "users", "select")
        assert exc.message == "Query failed"
        assert exc.details["table"] == "users"
        assert exc.details["operation"] == "select"


class TestRateLimitError:
    """Test rate limit error."""

    def test_rate_limit_error(self):
        """Test creating rate limit error."""
        exc = RateLimitError("Rate limit exceeded", "telegram", 60)
        assert exc.message == "Rate limit exceeded"
        assert exc.details["service"] == "telegram"
        assert exc.details["retry_after"] == 60


class TestNetworkError:
    """Test network error."""

    def test_network_error(self):
        """Test creating network error."""
        exc = NetworkError("Connection failed", "https://api.telegram.org", 500)
        assert exc.message == "Connection failed"
        assert exc.details["url"] == "https://api.telegram.org"
        assert exc.details["status_code"] == "500"
