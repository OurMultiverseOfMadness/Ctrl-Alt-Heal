"""Tests for error handling utilities."""

import pytest
from unittest.mock import Mock

from ctrl_alt_heal.utils.error_handling import (
    handle_errors,
    error_context,
    safe_execute,
    format_error_response,
    validate_required_fields,
    validate_field_type,
    handle_aws_error,
    retry_on_error,
)
from ctrl_alt_heal.utils.exceptions import (
    ValidationError,
    AWSServiceError,
)


class TestHandleErrors:
    """Test error handling decorator."""

    def test_handle_errors_success(self):
        """Test successful function execution."""

        @handle_errors()
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_handle_errors_custom_exception(self):
        """Test handling custom exception."""

        @handle_errors(reraise=False)
        def test_func():
            raise ValidationError("Invalid input", "field", "value")

        result = test_func()
        assert result["status"] == "error"
        assert "Invalid input" in result["message"]

    def test_handle_errors_unexpected_exception(self):
        """Test handling unexpected exception."""

        @handle_errors(reraise=False)
        def test_func():
            raise ValueError("Unexpected error")

        result = test_func()
        assert result["status"] == "error"
        assert result["message"] == "An error occurred"

    def test_handle_errors_reraise(self):
        """Test reraise behavior."""

        @handle_errors()
        def test_func():
            raise ValidationError("Invalid input")

        with pytest.raises(ValidationError):
            test_func()


class TestErrorContext:
    """Test error context manager."""

    def test_error_context_success(self):
        """Test successful operation."""
        with error_context("test operation"):
            result = "success"
        assert result == "success"

    def test_error_context_custom_exception(self):
        """Test handling custom exception in context."""
        with pytest.raises(ValidationError):
            with error_context("test operation"):
                raise ValidationError("Invalid input")

    def test_error_context_unexpected_exception(self):
        """Test handling unexpected exception in context."""
        with pytest.raises(ValueError):
            with error_context("test operation"):
                raise ValueError("Unexpected error")


class TestSafeExecute:
    """Test safe execute function."""

    def test_safe_execute_success(self):
        """Test successful function execution."""

        def test_func(a, b):
            return a + b

        result = safe_execute(test_func, 2, 3)
        assert result == 5

    def test_safe_execute_custom_exception(self):
        """Test handling custom exception."""

        def test_func():
            raise ValidationError("Invalid input")

        result = safe_execute(test_func, default_return="default")
        assert result == "default"

    def test_safe_execute_unexpected_exception(self):
        """Test handling unexpected exception."""

        def test_func():
            raise ValueError("Unexpected error")

        result = safe_execute(test_func, default_return="default")
        assert result == "default"


class TestFormatErrorResponse:
    """Test error response formatting."""

    def test_format_custom_exception(self):
        """Test formatting custom exception."""
        error = ValidationError("Invalid input", "field", "value")
        result = format_error_response(error)

        assert result["status"] == "error"
        assert result["message"] == "Invalid input"
        assert result["error_type"] == "ValidationError"

    def test_format_custom_exception_with_details(self):
        """Test formatting custom exception with details."""
        error = ValidationError("Invalid input", "field", "value")
        result = format_error_response(error, include_details=True)

        assert result["status"] == "error"
        assert result["message"] == "Invalid input"
        assert result["details"]["field"] == "field"
        assert result["details"]["value"] == "value"

    def test_format_generic_exception_user_friendly(self):
        """Test formatting generic exception with user-friendly message."""
        error = ValueError("Technical error")
        result = format_error_response(error, user_friendly=True)

        assert result["status"] == "error"
        assert result["message"] == "An unexpected error occurred. Please try again."
        assert result["error_type"] == "ValueError"

    def test_format_generic_exception_technical(self):
        """Test formatting generic exception with technical message."""
        error = ValueError("Technical error")
        result = format_error_response(error, user_friendly=False)

        assert result["status"] == "error"
        assert result["message"] == "Technical error"
        assert result["error_type"] == "ValueError"


class TestValidateRequiredFields:
    """Test required fields validation."""

    def test_validate_required_fields_success(self):
        """Test successful validation."""
        data = {"field1": "value1", "field2": "value2"}
        validate_required_fields(data, ["field1", "field2"])

    def test_validate_required_fields_missing(self):
        """Test validation with missing fields."""
        data = {"field1": "value1"}

        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, ["field1", "field2"])

        assert "field2" in str(exc_info.value)

    def test_validate_required_fields_none_value(self):
        """Test validation with None values."""
        data = {"field1": "value1", "field2": None}

        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, ["field1", "field2"])

        assert "field2" in str(exc_info.value)

    def test_validate_required_fields_custom_context(self):
        """Test validation with custom context."""
        data = {"field1": "value1"}

        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, ["field1", "field2"], "user data")

        assert "user data" in str(exc_info.value)


class TestValidateFieldType:
    """Test field type validation."""

    def test_validate_field_type_success(self):
        """Test successful type validation."""
        validate_field_type("test", str, "field_name")
        validate_field_type(123, int, "field_name")

    def test_validate_field_type_wrong_type(self):
        """Test type validation with wrong type."""
        with pytest.raises(ValidationError) as exc_info:
            validate_field_type("test", int, "field_name")

        assert "field_name" in str(exc_info.value)
        assert "int" in str(exc_info.value)

    def test_validate_field_type_none_not_allowed(self):
        """Test type validation with None not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            validate_field_type(None, str, "field_name")

        assert "field_name" in str(exc_info.value)
        assert "None" in str(exc_info.value)

    def test_validate_field_type_none_allowed(self):
        """Test type validation with None allowed."""
        validate_field_type(None, str, "field_name", allow_none=True)


class TestHandleAWSError:
    """Test AWS error handling."""

    def test_handle_aws_error_basic(self):
        """Test basic AWS error handling."""
        mock_error = Mock()
        mock_error.response = {"Error": {"Code": "AccessDenied"}}

        result = handle_aws_error(mock_error, "s3", "put_object")

        assert isinstance(result, AWSServiceError)
        assert "s3" in result.message
        assert "put_object" in result.message
        assert result.details["service"] == "s3"
        assert result.details["operation"] == "put_object"
        assert result.details["error_code"] == "AccessDenied"

    def test_handle_aws_error_with_context(self):
        """Test AWS error handling with context."""
        mock_error = Mock()
        mock_error.response = {"Error": {"Code": "NotFound"}}

        result = handle_aws_error(mock_error, "dynamodb", "get_item", "User not found")

        assert isinstance(result, AWSServiceError)
        assert "User not found" in result.message

    def test_handle_aws_error_no_response(self):
        """Test AWS error handling without response."""
        mock_error = Mock()
        mock_error.response = None

        result = handle_aws_error(mock_error, "s3", "put_object")

        assert isinstance(result, AWSServiceError)
        assert result.details["error_code"] is None


class TestRetryOnError:
    """Test retry decorator."""

    def test_retry_on_error_success_first_try(self):
        """Test successful execution on first try."""

        @retry_on_error(max_retries=3)
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_retry_on_error_success_after_retries(self):
        """Test successful execution after retries."""
        call_count = 0

        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 3

    def test_retry_on_error_max_retries_exceeded(self):
        """Test failure after max retries."""

        @retry_on_error(max_retries=2, delay=0.01)
        def test_func():
            raise ValueError("Persistent error")

        with pytest.raises(ValueError):
            test_func()

    def test_retry_on_error_specific_exception_types(self):
        """Test retry with specific exception types."""
        call_count = 0

        @retry_on_error(max_retries=2, delay=0.01, error_types=(ValueError,))
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 2

    def test_retry_on_error_other_exception_not_retried(self):
        """Test that other exceptions are not retried."""

        @retry_on_error(max_retries=2, delay=0.01, error_types=(ValueError,))
        def test_func():
            raise TypeError("Different error")

        with pytest.raises(TypeError):
            test_func()
