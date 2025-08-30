"""Input validation and sanitization for API boundaries."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ValidationError as PydanticValidationError,
    ConfigDict,
)

from ctrl_alt_heal.utils.exceptions import ValidationError
from ctrl_alt_heal.utils.validation import (
    validate_medication_name_with_exception,
    validate_schedule_times_with_exception,
    validate_schedule_duration_with_exception,
    validate_user_id_with_exception,
)
from ctrl_alt_heal.utils.timezone import validate_timezone_with_exception


class BaseRequestModel(BaseModel):
    """Base request model with common validation."""

    model_config = ConfigDict(
        extra="forbid",  # Reject extra fields
        validate_assignment=True,  # Validate on assignment
    )


class BaseResponseModel(BaseModel):
    """Base response model."""

    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")

    model_config = ConfigDict(extra="forbid")


class UserCreateRequest(BaseRequestModel):
    """Request model for creating a user."""

    user_id: str = Field(
        ..., min_length=1, max_length=100, description="User identifier"
    )
    username: Optional[str] = Field(None, max_length=100, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    language_code: Optional[str] = Field(
        None, max_length=10, description="Language code"
    )
    timezone: Optional[str] = Field(None, max_length=100, description="Timezone")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        try:
            validate_user_id_with_exception(v)
            return v
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        if v is not None:
            try:
                validate_timezone_with_exception(v)
                return v
            except Exception as e:
                raise ValueError(str(e))
        return v


class UserUpdateRequest(BaseRequestModel):
    """Request model for updating a user."""

    username: Optional[str] = Field(None, max_length=100, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    language_code: Optional[str] = Field(
        None, max_length=10, description="Language code"
    )
    timezone: Optional[str] = Field(None, max_length=100, description="Timezone")
    notes: Optional[str] = Field(None, max_length=1000, description="User notes")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        if v is not None:
            try:
                validate_timezone_with_exception(v)
                return v
            except Exception as e:
                raise ValueError(str(e))
        return v


class PrescriptionCreateRequest(BaseRequestModel):
    """Request model for creating a prescription."""

    user_id: str = Field(
        ..., min_length=1, max_length=100, description="User identifier"
    )
    name: str = Field(..., min_length=1, max_length=200, description="Medication name")
    dosage: str = Field(
        ..., min_length=1, max_length=100, description="Dosage information"
    )
    frequency: str = Field(
        ..., min_length=1, max_length=100, description="Frequency information"
    )
    instructions: Optional[str] = Field(
        None, max_length=500, description="Instructions"
    )
    prescriber: Optional[str] = Field(
        None, max_length=100, description="Prescriber name"
    )
    prescription_date: Optional[str] = Field(None, description="Prescription date")
    duration_days: Optional[int] = Field(
        None, ge=1, le=365, description="Duration in days"
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        try:
            validate_user_id_with_exception(v)
            return v
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("name")
    @classmethod
    def validate_medication_name(cls, v):
        try:
            validate_medication_name_with_exception(v)
            return v
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("prescription_date")
    @classmethod
    def validate_prescription_date(cls, v):
        if v is not None:
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
                return v
            except ValueError:
                raise ValueError("Invalid prescription date format")
        return v


class MedicationScheduleRequest(BaseRequestModel):
    """Request model for medication scheduling."""

    user_id: str = Field(
        ..., min_length=1, max_length=100, description="User identifier"
    )
    prescription_id: str = Field(
        ..., min_length=1, max_length=100, description="Prescription identifier"
    )
    times: List[str] = Field(
        ..., min_length=1, max_length=10, description="Schedule times"
    )
    duration_days: int = Field(..., ge=1, le=365, description="Duration in days")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        try:
            validate_user_id_with_exception(v)
            return v
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("times")
    @classmethod
    def validate_schedule_times(cls, v):
        try:
            validate_schedule_times_with_exception(v)
            return v
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("duration_days")
    @classmethod
    def validate_duration(cls, v):
        try:
            validate_schedule_duration_with_exception(v)
            return v
        except ValidationError as e:
            raise ValueError(str(e))


class MessageRequest(BaseRequestModel):
    """Request model for sending messages."""

    user_id: str = Field(
        ..., min_length=1, max_length=100, description="User identifier"
    )
    message: str = Field(
        ..., min_length=1, max_length=4096, description="Message content"
    )
    message_type: str = Field(
        default="text", pattern="^(text|photo|document)$", description="Message type"
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        try:
            validate_user_id_with_exception(v)
            return v
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v):
        # Basic sanitization
        v = re.sub(r"<script[^>]*>.*?</script>", "", v, flags=re.IGNORECASE | re.DOTALL)
        v = re.sub(r"<[^>]*>", "", v)  # Remove HTML tags
        v = v.strip()
        return v


class TimezoneRequest(BaseRequestModel):
    """Request model for timezone operations."""

    user_id: str = Field(
        ..., min_length=1, max_length=100, description="User identifier"
    )
    timezone: str = Field(..., min_length=1, max_length=100, description="Timezone")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        try:
            validate_user_id_with_exception(v)
            return v
        except ValidationError as e:
            raise ValueError(str(e))

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        try:
            validate_timezone_with_exception(v)
            return v
        except Exception as e:
            raise ValueError(str(e))


class SuccessResponse(BaseResponseModel):
    """Success response model."""

    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class ErrorResponse(BaseResponseModel):
    """Error response model."""

    error_type: str = Field(..., description="Error type")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")


class ValidationErrorResponse(BaseResponseModel):
    """Validation error response model."""

    errors: List[Dict[str, Any]] = Field(..., description="Validation errors")


def sanitize_input(
    data: Union[str, Dict[str, Any], List[Any]],
) -> Union[str, Dict[str, Any], List[Any]]:
    """
    Sanitize input data to prevent injection attacks.

    Args:
        data: Input data to sanitize

    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return _sanitize_string(data)
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
        return data


def _sanitize_string(value: str) -> str:
    """Sanitize a string value."""
    if not isinstance(value, str):
        return str(value)

    # Remove potentially dangerous characters and patterns
    sanitized = value

    # Remove script tags
    sanitized = re.sub(
        r"<script[^>]*>.*?</script>", "", sanitized, flags=re.IGNORECASE | re.DOTALL
    )

    # Remove other potentially dangerous HTML tags
    dangerous_tags = [
        "iframe",
        "object",
        "embed",
        "form",
        "input",
        "textarea",
        "select",
    ]
    for tag in dangerous_tags:
        sanitized = re.sub(
            rf"<{tag}[^>]*>.*?</{tag}>", "", sanitized, flags=re.IGNORECASE | re.DOTALL
        )
        sanitized = re.sub(rf"<{tag}[^>]*/?>", "", sanitized, flags=re.IGNORECASE)

    # Remove JavaScript event handlers
    sanitized = re.sub(
        r'\s*on\w+\s*=\s*["\'][^"\']*["\']', "", sanitized, flags=re.IGNORECASE
    )

    # Remove CSS expressions
    sanitized = re.sub(r"expression\s*\([^)]*\)", "", sanitized, flags=re.IGNORECASE)

    # Remove SQL injection patterns
    sql_patterns = [
        r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
        r"(\b(or|and)\b\s+\d+\s*=\s*\d+)",
        r"(\b(union|select|insert|update|delete|drop|create|alter)\b\s+.*\bfrom\b)",
    ]
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    # Remove command injection patterns
    cmd_patterns = [
        r"(\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ipconfig)\b)",
        r"(\b(rm|del|mkdir|touch|chmod|chown)\b)",
        r"(\b(echo|printf|grep|sed|awk|cut|sort|uniq)\b)",
    ]
    for pattern in cmd_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    # Remove null bytes and control characters
    sanitized = sanitized.replace("\x00", "")
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", sanitized)

    # Normalize whitespace
    sanitized = re.sub(r"\s+", " ", sanitized)
    sanitized = sanitized.strip()

    return sanitized


def validate_request_data(data: Dict[str, Any], model_class: type) -> Dict[str, Any]:
    """
    Validate and sanitize request data using Pydantic models.

    Args:
        data: Request data to validate
        model_class: Pydantic model class for validation

    Returns:
        Validated and sanitized data

    Raises:
        ValidationError: If validation fails
    """
    try:
        # Sanitize input data
        sanitized_data = sanitize_input(data)

        # Validate using Pydantic model
        validated_model = model_class(**sanitized_data)  # type: ignore

        # Return validated data as dict
        return validated_model.model_dump()

    except PydanticValidationError as e:
        errors = []
        for error in e.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
        raise ValidationError("Validation failed", field="validation", value=errors)
    except Exception as e:
        raise ValidationError(f"Validation error: {str(e)}")


def create_error_response(
    error: Exception, include_details: bool = False
) -> Dict[str, Any]:
    """
    Create standardized error response.

    Args:
        error: Exception that occurred
        include_details: Whether to include error details

    Returns:
        Error response dictionary
    """
    if isinstance(error, ValidationError):
        # Handle ValidationError with field/value structure
        if hasattr(error, "details") and error.details:
            field = error.details.get("field", "unknown")
            value = error.details.get("value")
            errors = [{"field": field, "message": str(error), "value": value}]
        else:
            errors = [{"field": "unknown", "message": str(error)}]

        return ValidationErrorResponse(
            status="error", message="Validation failed", errors=errors
        ).model_dump()

    details = None
    if include_details and hasattr(error, "details") and error.details:
        details = error.details

    response = ErrorResponse(
        status="error",
        message=str(error),
        error_type=type(error).__name__,
        details=details,
    )

    return response.model_dump()


def create_success_response(
    data: Optional[Dict[str, Any]] = None, message: str = "Success"
) -> Dict[str, Any]:
    """
    Create standardized success response.

    Args:
        data: Response data
        message: Success message

    Returns:
        Success response dictionary
    """
    return SuccessResponse(status="success", message=message, data=data).model_dump()
