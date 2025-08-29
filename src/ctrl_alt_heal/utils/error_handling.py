"""Error handling utilities for consistent error management."""

from __future__ import annotations

import functools
import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, Type, Union

from ctrl_alt_heal.utils.exceptions import (
    CtrlAltHealException,
    AWSServiceError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def handle_errors(
    error_types: Optional[Union[Type[Exception], tuple[Type[Exception], ...]]] = None,
    default_message: str = "An error occurred",
    log_error: bool = True,
    reraise: bool = True,
) -> Callable:
    """
    Decorator for consistent error handling.

    Args:
        error_types: Exception types to catch (default: all CtrlAltHealException)
        default_message: Default error message if none provided
        log_error: Whether to log the error
        reraise: Whether to reraise the exception

    Returns:
        Decorated function
    """
    if error_types is None:
        error_types = CtrlAltHealException

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)

                if not reraise:
                    return {"status": "error", "message": str(e) or default_message}
                raise
            except Exception as e:
                if log_error:
                    logger.error(
                        f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True
                    )

                if not reraise:
                    return {"status": "error", "message": default_message}
                raise

        return wrapper

    return decorator


@contextmanager
def error_context(
    operation: str,
    error_types: Optional[Union[Type[Exception], tuple[Type[Exception], ...]]] = None,
    default_message: str = "Operation failed",
    log_error: bool = True,
):
    """
    Context manager for error handling.

    Args:
        operation: Name of the operation being performed
        error_types: Exception types to catch
        default_message: Default error message
        log_error: Whether to log errors

    Yields:
        None
    """
    if error_types is None:
        error_types = CtrlAltHealException

    try:
        yield
    except error_types as e:
        if log_error:
            logger.error(f"Error during {operation}: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        if log_error:
            logger.error(
                f"Unexpected error during {operation}: {str(e)}", exc_info=True
            )
        raise


def safe_execute(
    func: Callable,
    *args,
    error_types: Optional[Union[Type[Exception], tuple[Type[Exception], ...]]] = None,
    default_return: Any = None,
    log_error: bool = True,
    **kwargs,
) -> Any:
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Function arguments
        error_types: Exception types to catch
        default_return: Value to return on error
        log_error: Whether to log errors
        **kwargs: Function keyword arguments

    Returns:
        Function result or default_return on error
    """
    if error_types is None:
        error_types = CtrlAltHealException

    try:
        return func(*args, **kwargs)
    except error_types as e:
        if log_error:
            logger.error(f"Error executing {func.__name__}: {str(e)}", exc_info=True)
        return default_return
    except Exception as e:
        if log_error:
            logger.error(
                f"Unexpected error executing {func.__name__}: {str(e)}", exc_info=True
            )
        return default_return


def format_error_response(
    error: Exception, include_details: bool = False, user_friendly: bool = True
) -> Dict[str, Any]:
    """
    Format an error into a standardized response.

    Args:
        error: The exception that occurred
        include_details: Whether to include error details
        user_friendly: Whether to use user-friendly messages

    Returns:
        Formatted error response
    """
    if isinstance(error, CtrlAltHealException):
        response = {
            "status": "error",
            "message": error.message,
            "error_type": error.__class__.__name__,
        }
        if include_details:
            response["details"] = error.details
    else:
        if user_friendly:
            message = "An unexpected error occurred. Please try again."
        else:
            message = str(error)

        response = {
            "status": "error",
            "message": message,
            "error_type": error.__class__.__name__,
        }

    return response


def validate_required_fields(
    data: Dict[str, Any], required_fields: list[str], context: str = "input data"
) -> None:
    """
    Validate that required fields are present in data.

    Args:
        data: Data to validate
        required_fields: List of required field names
        context: Context for error messages

    Raises:
        ValidationError: If required fields are missing
    """
    missing_fields = [
        field for field in required_fields if field not in data or data[field] is None
    ]

    if missing_fields:
        raise ValidationError(
            f"Missing required fields in {context}: {', '.join(missing_fields)}",
            field=",".join(missing_fields),
        )


def validate_field_type(
    value: Any, expected_type: Type, field_name: str, allow_none: bool = False
) -> None:
    """
    Validate that a field has the expected type.

    Args:
        value: Value to validate
        expected_type: Expected type
        field_name: Name of the field
        allow_none: Whether None values are allowed

    Raises:
        ValidationError: If type validation fails
    """
    if value is None and allow_none:
        return

    if value is None and not allow_none:
        raise ValidationError(f"Field '{field_name}' cannot be None", field=field_name)

    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Field '{field_name}' must be of type {expected_type.__name__}, got {type(value).__name__}",
            field=field_name,
            value=value,
        )


def handle_aws_error(
    error: Exception, service: str, operation: str, context: Optional[str] = None
) -> AWSServiceError:
    """
    Convert AWS errors to standardized AWSServiceError.

    Args:
        error: Original AWS error
        service: AWS service name
        operation: Operation being performed
        context: Additional context

    Returns:
        AWSServiceError with standardized format
    """
    error_message = f"AWS {service} {operation} failed"
    if context:
        error_message += f": {context}"

    # Extract error code if available
    error_code = None
    if hasattr(error, "response") and hasattr(error.response, "get"):
        error_code = error.response.get("Error", {}).get("Code")

    return AWSServiceError(
        message=error_message,
        service=service,
        operation=operation,
        error_code=error_code,
    )


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    error_types: Optional[Union[Type[Exception], tuple[Type[Exception], ...]]] = None,
) -> Callable:
    """
    Decorator to retry functions on specific errors.

    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff_factor: Factor to increase delay on each retry
        error_types: Exception types to retry on

    Returns:
        Decorated function
    """
    if error_types is None:
        error_types = (Exception,)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except error_types as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}"
                        )

            raise last_exception

        return wrapper

    return decorator
