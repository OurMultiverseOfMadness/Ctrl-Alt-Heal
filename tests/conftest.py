"""Pytest configuration and fixtures for Ctrl-Alt-Heal tests."""

import os
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables before each test."""
    # Set required environment variables for tests
    test_env_vars = {
        "UPLOADS_BUCKET_NAME": "test-uploads-bucket",
        "TELEGRAM_SECRET_NAME": "test-telegram-secret",
        "DATABASE_TABLE_NAME": "test-table",
        "CONVERSATIONS_TABLE_NAME": "test-conversations-table",
        "BEDROCK_MODEL_ID": "test-model",
        "BEDROCK_MULTIMODAL_MODEL_ID": "test-multimodal-model",
        "GOOGLE_CLIENT_SECRETS_FILE": "test-client-secret.json",
        "GOOGLE_REDIRECT_URI": "https://test-redirect-uri.com/oauth2callback",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "test-access-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key",
    }

    # Store original environment variables
    original_env = {}
    for key in test_env_vars:
        if key in os.environ:
            original_env[key] = os.environ[key]

    # Set test environment variables
    for key, value in test_env_vars.items():
        os.environ[key] = value

    yield

    # Restore original environment variables
    for key in test_env_vars:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            os.environ.pop(key, None)


@pytest.fixture
def mock_aws_services():
    """Mock AWS services for testing."""
    with patch("boto3.client") as mock_boto3_client:
        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.put_object.return_value = {"ETag": "test-etag"}
        mock_s3.get_object.return_value = {"Body": Mock()}

        # Mock DynamoDB client
        mock_dynamodb = Mock()
        mock_dynamodb.put_item.return_value = {}
        mock_dynamodb.get_item.return_value = {"Item": {}}
        mock_dynamodb.query.return_value = {"Items": []}

        # Mock Bedrock client
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = {
            "body": Mock(read=lambda: b'{"test": "response"}')
        }

        # Mock Secrets Manager client
        mock_secrets = Mock()
        mock_secrets.get_secret_value.return_value = {
            "SecretString": '{"test": "secret"}'
        }

        # Configure boto3.client to return appropriate mocks
        def mock_client(service_name, **kwargs):
            if service_name == "s3":
                return mock_s3
            elif service_name == "dynamodb":
                return mock_dynamodb
            elif service_name == "bedrock-runtime":
                return mock_bedrock
            elif service_name == "secretsmanager":
                return mock_secrets
            else:
                return Mock()

        mock_boto3_client.side_effect = mock_client

        yield {
            "s3": mock_s3,
            "dynamodb": mock_dynamodb,
            "bedrock": mock_bedrock,
            "secrets": mock_secrets,
        }


@pytest.fixture
def mock_telegram():
    """Mock Telegram API for testing."""
    with patch(
        "ctrl_alt_heal.infrastructure.telegram_client.requests.post"
    ) as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "user_id": "test_user_123",
        "chat_id": "test_chat_123",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en",
        "timezone": "UTC",
        "created_at": "2024-01-01T00:00:00Z",
        "last_active": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_prescription_data() -> Dict[str, Any]:
    """Sample prescription data for testing."""
    return {
        "medication_name": "Test Medication",
        "dosage": "10mg",
        "frequency": "twice daily",
        "duration": "7 days",
        "instructions": "Take with food",
        "prescriber": "Dr. Test",
        "prescription_date": "2024-01-01",
    }
