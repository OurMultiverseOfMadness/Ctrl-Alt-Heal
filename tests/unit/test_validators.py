"""Tests for input validation and sanitization."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from ctrl_alt_heal.api.validators import (
    UserCreateRequest,
    UserUpdateRequest,
    PrescriptionCreateRequest,
    MedicationScheduleRequest,
    MessageRequest,
    TimezoneRequest,
    SuccessResponse,
    ErrorResponse,
    ValidationErrorResponse,
    sanitize_input,
    validate_request_data,
    create_error_response,
    create_success_response,
)
from ctrl_alt_heal.utils.exceptions import ValidationError


class TestUserCreateRequest:
    """Test user creation request validation."""

    def test_valid_user_create_request(self):
        """Test valid user creation request."""
        data = {
            "user_id": "user123",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "language_code": "en",
            "timezone": "America/New_York",
        }

        request = UserCreateRequest(**data)
        assert request.user_id == "user123"
        assert request.username == "testuser"
        assert request.first_name == "Test"
        assert request.last_name == "User"
        assert request.language_code == "en"
        assert request.timezone == "America/New_York"

    def test_invalid_user_id(self):
        """Test invalid user ID."""
        data = {
            "user_id": "",  # Empty user ID
            "username": "testuser",
        }

        with pytest.raises(PydanticValidationError):
            UserCreateRequest(**data)

    def test_invalid_timezone(self):
        """Test invalid timezone."""
        data = {"user_id": "user123", "timezone": "Invalid/Timezone"}

        with pytest.raises(PydanticValidationError) as exc_info:
            UserCreateRequest(**data)
        assert "Invalid timezone" in str(exc_info.value)

    def test_optional_fields(self):
        """Test optional fields."""
        data = {"user_id": "user123"}

        request = UserCreateRequest(**data)
        assert request.user_id == "user123"
        assert request.username is None
        assert request.first_name is None
        assert request.last_name is None
        assert request.language_code is None
        assert request.timezone is None


class TestUserUpdateRequest:
    """Test user update request validation."""

    def test_valid_user_update_request(self):
        """Test valid user update request."""
        data = {
            "username": "updateduser",
            "first_name": "Updated",
            "last_name": "User",
            "language_code": "es",
            "timezone": "Europe/London",
            "notes": "Updated user notes",
        }

        request = UserUpdateRequest(**data)
        assert request.username == "updateduser"
        assert request.first_name == "Updated"
        assert request.last_name == "User"
        assert request.language_code == "es"
        assert request.timezone == "Europe/London"
        assert request.notes == "Updated user notes"

    def test_all_optional_fields(self):
        """Test all optional fields."""
        data = {}

        request = UserUpdateRequest(**data)
        assert request.username is None
        assert request.first_name is None
        assert request.last_name is None
        assert request.language_code is None
        assert request.timezone is None
        assert request.notes is None


class TestPrescriptionCreateRequest:
    """Test prescription creation request validation."""

    def test_valid_prescription_create_request(self):
        """Test valid prescription creation request."""
        data = {
            "user_id": "user123",
            "name": "Aspirin",
            "dosage": "100mg",
            "frequency": "Twice daily",
            "instructions": "Take with food",
            "prescriber": "Dr. Smith",
            "prescription_date": "2024-01-15T10:00:00Z",
            "duration_days": 30,
        }

        request = PrescriptionCreateRequest(**data)
        assert request.user_id == "user123"
        assert request.name == "Aspirin"
        assert request.dosage == "100mg"
        assert request.frequency == "Twice daily"
        assert request.instructions == "Take with food"
        assert request.prescriber == "Dr. Smith"
        assert request.prescription_date == "2024-01-15T10:00:00Z"
        assert request.duration_days == 30

    def test_invalid_medication_name(self):
        """Test invalid medication name."""
        data = {
            "user_id": "user123",
            "name": "",  # Empty name
            "dosage": "100mg",
            "frequency": "Twice daily",
        }

        with pytest.raises(PydanticValidationError):
            PrescriptionCreateRequest(**data)

    def test_invalid_prescription_date(self):
        """Test invalid prescription date."""
        data = {
            "user_id": "user123",
            "name": "Aspirin",
            "dosage": "100mg",
            "frequency": "Twice daily",
            "prescription_date": "invalid-date",
        }

        with pytest.raises(PydanticValidationError):
            PrescriptionCreateRequest(**data)

    def test_invalid_duration_days(self):
        """Test invalid duration days."""
        data = {
            "user_id": "user123",
            "name": "Aspirin",
            "dosage": "100mg",
            "frequency": "Twice daily",
            "duration_days": 0,  # Invalid duration
        }

        with pytest.raises(PydanticValidationError):
            PrescriptionCreateRequest(**data)


class TestMedicationScheduleRequest:
    """Test medication schedule request validation."""

    def test_valid_medication_schedule_request(self):
        """Test valid medication schedule request."""
        data = {
            "user_id": "user123",
            "prescription_id": "presc123",
            "times": ["08:00", "20:00"],
            "duration_days": 14,
        }

        request = MedicationScheduleRequest(**data)
        assert request.user_id == "user123"
        assert request.prescription_id == "presc123"
        assert request.times == ["08:00", "20:00"]
        assert request.duration_days == 14

    def test_empty_times_list(self):
        """Test empty times list."""
        data = {
            "user_id": "user123",
            "prescription_id": "presc123",
            "times": [],  # Empty list
            "duration_days": 14,
        }

        with pytest.raises(PydanticValidationError):
            MedicationScheduleRequest(**data)

    def test_too_many_times(self):
        """Test too many times."""
        data = {
            "user_id": "user123",
            "prescription_id": "presc123",
            "times": [
                "08:00",
                "12:00",
                "16:00",
                "20:00",
                "00:00",
                "04:00",
                "06:00",
                "10:00",
                "14:00",
                "18:00",
                "22:00",
            ],  # 11 times
            "duration_days": 14,
        }

        with pytest.raises(PydanticValidationError):
            MedicationScheduleRequest(**data)


class TestMessageRequest:
    """Test message request validation."""

    def test_valid_message_request(self):
        """Test valid message request."""
        data = {
            "user_id": "user123",
            "message": "Hello, world!",
            "message_type": "text",
        }

        request = MessageRequest(**data)
        assert request.user_id == "user123"
        assert request.message == "Hello, world!"
        assert request.message_type == "text"

    def test_default_message_type(self):
        """Test default message type."""
        data = {"user_id": "user123", "message": "Hello, world!"}

        request = MessageRequest(**data)
        assert request.message_type == "text"

    def test_invalid_message_type(self):
        """Test invalid message type."""
        data = {
            "user_id": "user123",
            "message": "Hello, world!",
            "message_type": "invalid",
        }

        with pytest.raises(PydanticValidationError):
            MessageRequest(**data)

    def test_message_sanitization(self):
        """Test message sanitization."""
        data = {
            "user_id": "user123",
            "message": "<script>alert('xss')</script>Hello, world!<p>Test</p>",
        }

        request = MessageRequest(**data)
        assert "script" not in request.message
        assert "alert" not in request.message
        assert "Hello, world!" in request.message


class TestTimezoneRequest:
    """Test timezone request validation."""

    def test_valid_timezone_request(self):
        """Test valid timezone request."""
        data = {"user_id": "user123", "timezone": "America/New_York"}

        request = TimezoneRequest(**data)
        assert request.user_id == "user123"
        assert request.timezone == "America/New_York"

    def test_invalid_timezone(self):
        """Test invalid timezone."""
        data = {"user_id": "user123", "timezone": "Invalid/Timezone"}

        with pytest.raises(PydanticValidationError) as exc_info:
            TimezoneRequest(**data)
        assert "Invalid timezone" in str(exc_info.value)


class TestResponseModels:
    """Test response models."""

    def test_success_response(self):
        """Test success response model."""
        data = {"user_id": "user123", "status": "active"}
        response = SuccessResponse(
            status="success", message="User created successfully", data=data
        )

        assert response.status == "success"
        assert response.message == "User created successfully"
        assert response.data == data

    def test_error_response(self):
        """Test error response model."""
        details = {"field": "user_id", "reason": "Already exists"}
        response = ErrorResponse(
            status="error",
            message="User already exists",
            error_type="ValidationError",
            details=details,
        )

        assert response.status == "error"
        assert response.message == "User already exists"
        assert response.error_type == "ValidationError"
        assert response.details == details

    def test_validation_error_response(self):
        """Test validation error response model."""
        errors = [
            {"field": "user_id", "message": "Required field", "type": "missing"},
            {"field": "email", "message": "Invalid format", "type": "value_error"},
        ]
        response = ValidationErrorResponse(
            status="error", message="Validation failed", errors=errors
        )

        assert response.status == "error"
        assert response.message == "Validation failed"
        assert response.errors == errors


class TestSanitizeInput:
    """Test input sanitization."""

    def test_sanitize_string(self):
        """Test string sanitization."""
        # Test XSS prevention
        malicious_input = "<script>alert('xss')</script>Hello, world!"
        sanitized = sanitize_input(malicious_input)
        assert "script" not in sanitized
        assert "alert" not in sanitized
        assert "Hello, world!" in sanitized

    def test_sanitize_sql_injection(self):
        """Test SQL injection prevention."""
        malicious_input = "'; DROP TABLE users; --"
        sanitized = sanitize_input(malicious_input)
        assert "DROP TABLE" not in sanitized
        # Note: "users" is not removed as it's a common word, but SQL keywords are removed

    def test_sanitize_command_injection(self):
        """Test command injection prevention."""
        malicious_input = "test; rm -rf /; echo 'hacked'"
        sanitized = sanitize_input(malicious_input)
        assert "rm -rf" not in sanitized
        assert "echo" not in sanitized

    def test_sanitize_dict(self):
        """Test dictionary sanitization."""
        data = {"name": "<script>alert('xss')</script>John", "message": "Hello, world!"}
        sanitized = sanitize_input(data)
        assert "script" not in sanitized["name"]
        assert sanitized["message"] == "Hello, world!"

    def test_sanitize_list(self):
        """Test list sanitization."""
        data = [
            "<script>alert('xss')</script>",
            "Hello, world!",
            {"key": "<iframe>malicious</iframe>"},
        ]
        sanitized = sanitize_input(data)
        assert "script" not in sanitized[0]
        assert sanitized[1] == "Hello, world!"
        assert "iframe" not in sanitized[2]["key"]

    def test_sanitize_non_string(self):
        """Test sanitization of non-string values."""
        data = 123
        sanitized = sanitize_input(data)
        assert sanitized == 123

    def test_sanitize_control_characters(self):
        """Test sanitization of control characters."""
        malicious_input = "Hello\x00World\x08\x0c\x0e\x1f"
        sanitized = sanitize_input(malicious_input)
        assert "\x00" not in sanitized
        assert "\x08" not in sanitized
        assert "Hello" in sanitized
        assert "World" in sanitized


class TestValidateRequestData:
    """Test request data validation."""

    def test_valid_request_data(self):
        """Test valid request data validation."""
        data = {
            "user_id": "user123",
            "username": "testuser",
            "timezone": "America/New_York",
        }

        validated_data = validate_request_data(data, UserCreateRequest)
        assert validated_data["user_id"] == "user123"
        assert validated_data["username"] == "testuser"
        assert validated_data["timezone"] == "America/New_York"

    def test_invalid_request_data(self):
        """Test invalid request data validation."""
        data = {
            "user_id": "",  # Invalid user ID
            "username": "testuser",
        }

        with pytest.raises(ValidationError):
            validate_request_data(data, UserCreateRequest)

    def test_sanitized_request_data(self):
        """Test that request data is sanitized."""
        data = {
            "user_id": "user123",
            "message": "<script>alert('xss')</script>Hello, world!",
        }

        validated_data = validate_request_data(data, MessageRequest)
        assert "script" not in validated_data["message"]
        assert "Hello, world!" in validated_data["message"]


class TestCreateErrorResponse:
    """Test error response creation."""

    def test_create_validation_error_response(self):
        """Test creating validation error response."""
        error = ValidationError(
            "Validation failed",
            field="validation",
            value=[{"field": "user_id", "message": "Required field"}],
        )

        response = create_error_response(error)
        assert response["status"] == "error"
        assert response["message"] == "Validation failed"
        assert "errors" in response

    def test_create_generic_error_response(self):
        """Test creating generic error response."""
        error = ValueError("Something went wrong")

        response = create_error_response(error)
        assert response["status"] == "error"
        assert response["message"] == "Something went wrong"
        assert response["error_type"] == "ValueError"

    def test_create_error_response_with_details(self):
        """Test creating error response with details."""
        error = ValidationError("Validation failed", field="user_id", value="invalid")

        response = create_error_response(error, include_details=True)
        assert response["status"] == "error"
        assert response["errors"][0]["field"] == "user_id"
        assert response["errors"][0]["value"] == "invalid"


class TestCreateSuccessResponse:
    """Test success response creation."""

    def test_create_success_response_with_data(self):
        """Test creating success response with data."""
        data = {"user_id": "user123", "status": "active"}

        response = create_success_response(data, "User created successfully")
        assert response["status"] == "success"
        assert response["message"] == "User created successfully"
        assert response["data"] == data

    def test_create_success_response_without_data(self):
        """Test creating success response without data."""
        response = create_success_response()
        assert response["status"] == "success"
        assert response["message"] == "Success"
        assert response["data"] is None

    def test_create_success_response_custom_message(self):
        """Test creating success response with custom message."""
        response = create_success_response(message="Operation completed")
        assert response["status"] == "success"
        assert response["message"] == "Operation completed"
