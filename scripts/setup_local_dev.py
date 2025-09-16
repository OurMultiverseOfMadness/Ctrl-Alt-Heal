#!/usr/bin/env python3
"""
Local development setup script for Ctrl-Alt-Heal.

This script helps set up a local development environment with mock services
and local alternatives to AWS services.
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def create_local_env():
    """Create a local development environment file."""
    print("🔄 Creating local development environment file...")

    local_env_content = """# Local Development Environment Configuration
# This file is for local development only

# =============================================================================
# Local Development Settings
# =============================================================================
ENVIRONMENT=local
PROJECT_NAME=CtrlAltHeal
AWS_REGION=ap-southeast-1

# =============================================================================
# Local Service Endpoints (for development)
# =============================================================================
# Use local alternatives or mock services
DYNAMODB_ENDPOINT=http://localhost:8000
S3_ENDPOINT=http://localhost:9000
SECRETS_ENDPOINT=http://localhost:4566

# =============================================================================
# Local Database Configuration
# =============================================================================
USERS_TABLE_NAME=ctrl_alt_heal_local_user_profiles
CONVERSATIONS_TABLE_NAME=ctrl_alt_heal_local_conversation_history
PRESCRIPTIONS_TABLE_NAME=ctrl_alt_heal_local_prescriptions
IDENTITIES_TABLE_NAME=ctrl_alt_heal_local_identities
FHIR_DATA_TABLE_NAME=ctrl_alt_heal_local_fhir_data

# =============================================================================
# Local Storage Configuration
# =============================================================================
UPLOADS_BUCKET_NAME=ctrl-alt-heal-local-uploads
ASSETS_BUCKET_NAME=ctrl-alt-heal-local-assets

# =============================================================================
# Secrets Configuration (for local development)
# =============================================================================
# These should be set to your actual values for local testing
TELEGRAM_SECRET_NAME=local/telegram/bot-token
SERPER_SECRET_NAME=local/serper/api-key

# =============================================================================
# AI Model Configuration
# =============================================================================
BEDROCK_MODEL_ID=apac.amazon.nova-lite-v1:0
BEDROCK_MULTIMODAL_MODEL_ID=apac.amazon.nova-lite-v1:0
BEDROCK_REGION=ap-southeast-1

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_LEVEL=DEBUG

# =============================================================================
# Development Flags
# =============================================================================
LOCAL_DEVELOPMENT=true
MOCK_AWS_SERVICES=true

# =============================================================================
# Mock Mode Configuration
# =============================================================================
# When MOCK_AWS_SERVICES=true, the application will use mock implementations
# instead of real AWS services, allowing development without AWS access
# - Mock Bedrock: Returns mock AI responses
# - Mock Prescription Extraction: Returns sample prescription data
# - Mock Image Description: Returns sample image descriptions
"""

    with open(".env.local", "w") as f:
        f.write(local_env_content)

    print("✅ Created .env.local file")


def setup_localstack():
    """Set up LocalStack for local AWS services."""
    print("🔄 Setting up LocalStack for local AWS services...")

    # Check if Docker is running
    if not run_command("docker --version", "Checking Docker"):
        print("❌ Docker is not installed or not running")
        print("Please install Docker and try again")
        return False

    # Start LocalStack
    localstack_cmd = """
    docker run -d \\
        --name localstack \\
        -p 4566:4566 \\
        -p 8000:8000 \\
        -e SERVICES=dynamodb,s3,secretsmanager \\
        -e DEBUG=1 \\
        localstack/localstack
    """

    if run_command(localstack_cmd, "Starting LocalStack"):
        print("✅ LocalStack started successfully")
        print("📋 LocalStack services available at:")
        print("   - DynamoDB: http://localhost:8000")
        print("   - S3: http://localhost:4566")
        print("   - Secrets Manager: http://localhost:4566")
        return True
    else:
        print("❌ Failed to start LocalStack")
        return False


def create_local_tables():
    """Create local DynamoDB tables."""
    print("🔄 Creating local DynamoDB tables...")

    # Wait for LocalStack to be ready
    import time

    time.sleep(5)

    tables = [
        "ctrl_alt_heal_local_user_profiles",
        "ctrl_alt_heal_local_conversation_history",
        "ctrl_alt_heal_local_prescriptions",
        "ctrl_alt_heal_local_identities",
        "ctrl_alt_heal_local_fhir_data",
    ]

    for table in tables:
        cmd = f"""
        aws dynamodb create-table \\
            --table-name {table} \\
            --attribute-definitions \\
                AttributeName=id,AttributeType=S \\
            --key-schema \\
                AttributeName=id,KeyType=HASH \\
            --billing-mode PAY_PER_REQUEST \\
            --endpoint-url http://localhost:8000 \\
            --region us-east-1
        """

        if run_command(cmd, f"Creating table {table}"):
            print(f"✅ Created table {table}")
        else:
            print(f"❌ Failed to create table {table}")


def main():
    """Main setup function."""
    print("🚀 Setting up Ctrl-Alt-Heal local development environment...")
    print("=" * 60)

    # Create local environment file
    create_local_env()

    # Ask user if they want to set up LocalStack
    print("\n🤔 Do you want to set up LocalStack for local AWS services?")
    print("This will start Docker containers for DynamoDB, S3, and Secrets Manager")
    response = input("Set up LocalStack? (y/n): ").lower().strip()

    if response in ["y", "yes"]:
        if setup_localstack():
            create_local_tables()
        else:
            print(
                "⚠️  LocalStack setup failed. You can still run the app with real AWS services."
            )
    else:
        print("ℹ️  Skipping LocalStack setup. You'll need to use real AWS services.")

    print("\n" + "=" * 60)
    print("🎉 Local development setup complete!")
    print("\n📋 Next steps:")
    print("1. Copy your actual API keys to .env.local:")
    print("   - Set TELEGRAM_BOT_TOKEN to your actual bot token")
    print("   - Set SERPER_API_KEY to your actual API key")
    print("\n2. Start the local development server:")
    print("   python scripts/local_webhook.py")
    print("\n3. Test the application:")
    print("   curl http://localhost:8000/health")
    print("\n4. For Telegram webhook testing, use ngrok:")
    print("   ngrok http 8000")
    print("   # Then set webhook URL in Telegram")


if __name__ == "__main__":
    main()
