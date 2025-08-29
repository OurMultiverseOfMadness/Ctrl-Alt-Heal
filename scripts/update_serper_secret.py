#!/usr/bin/env python3
"""
Script to update the Serper API key in AWS Secrets Manager.
Run this after deploying the CDK stack to set your actual Serper API key.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError


def update_serper_secret(api_key: str, region: str = "ap-southeast-1"):
    """Update the Serper API key in AWS Secrets Manager."""

    # Create Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region)

    secret_name = "CtrlAltHealSerperSecret"
    secret_value = json.dumps({"api_key": api_key})

    try:
        # Update the secret
        response = client.update_secret(SecretId=secret_name, SecretString=secret_value)
        print(f"✅ Successfully updated Serper API key in secret: {secret_name}")
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
        print("Usage: python scripts/update_serper_secret.py <your_serper_api_key>")
        print("\nTo get a Serper API key:")
        print("1. Go to https://serper.dev")
        print("2. Sign up for an account")
        print("3. Get your API key from the dashboard")
        sys.exit(1)

    api_key = sys.argv[1]

    if not api_key or len(api_key) < 10:
        print("❌ Invalid API key provided. Please provide a valid Serper API key.")
        sys.exit(1)

    print("🔄 Updating Serper API key in AWS Secrets Manager...")

    if update_serper_secret(api_key):
        print("\n🎉 Serper API key updated successfully!")
        print("The search tool should now work properly.")
    else:
        print("\n❌ Failed to update Serper API key.")
        sys.exit(1)


if __name__ == "__main__":
    main()
