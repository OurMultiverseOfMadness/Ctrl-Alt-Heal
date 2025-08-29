#!/usr/bin/env python3
"""
Script to update the Telegram bot token in AWS Secrets Manager.
Run this after deploying the CDK stack to set your actual Telegram bot token.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError


def update_telegram_secret(bot_token: str, region: str = "ap-southeast-1"):
    """Update the Telegram bot token in AWS Secrets Manager."""

    # Create Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region)

    secret_name = "ctrl-alt-heal/telegram/bot-token"
    secret_value = json.dumps({"value": bot_token})

    try:
        # Update the secret
        response = client.update_secret(SecretId=secret_name, SecretString=secret_value)
        print(f"✅ Successfully updated Telegram bot token in secret: {secret_name}")
        print(f"Secret ARN: {response['ARN']}")
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            print(
                f"❌ Secret '{secret_name}' not found. Make sure you've deployed the CDK stack first."
            )
        else:
            print(f"❌ Error updating secret: {e}")
        return False


def main():
    """Main function to handle command line arguments."""

    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/update_telegram_secret.py <your_telegram_bot_token>"
        )
        print("\nTo get a Telegram bot token:")
        print("1. Message @BotFather on Telegram")
        print("2. Use /newbot command to create a new bot")
        print("3. Get your bot token from the response")
        sys.exit(1)

    bot_token = sys.argv[1]

    if not bot_token or len(bot_token) < 20:
        print(
            "❌ Invalid bot token provided. Please provide a valid Telegram bot token."
        )
        sys.exit(1)

    print("🔄 Updating Telegram bot token in AWS Secrets Manager...")

    if update_telegram_secret(bot_token):
        print("\n🎉 Telegram bot token updated successfully!")
        print("The Telegram integration should now work properly.")
    else:
        print("\n❌ Failed to update Telegram bot token.")
        sys.exit(1)


if __name__ == "__main__":
    main()
