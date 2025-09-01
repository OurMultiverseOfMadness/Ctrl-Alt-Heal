#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.fargate_stack import FargateStack
from stacks.secrets_stack import SecretsStack

app = cdk.App()

# Get environment configuration from environment variables or use defaults
aws_account = os.environ.get("CDK_DEFAULT_ACCOUNT", "056445322359")
aws_region = os.environ.get("CDK_DEFAULT_REGION", "ap-southeast-1")

# Define the AWS environment
aws_env = cdk.Environment(account=aws_account, region=aws_region)

# Get stack configuration
environment = os.environ.get("ENVIRONMENT", "production")
project_name = os.environ.get("PROJECT_NAME", "Cara-Agents")

# Create the secrets stack
secrets_stack = SecretsStack(
    app,
    f"{project_name}SecretsStack",
    env=aws_env,
    environment=environment,
)

# Create the Fargate stack without database dependency
fargate_stack = FargateStack(
    app,
    f"{project_name}FargateStack",
    database_stack=None,  # No database dependency
    secrets_stack=secrets_stack,
    env=aws_env,
    environment=environment,
)

app.synth()
