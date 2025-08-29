#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.api_gateway_stack import ApiGatewayStack
from stacks.database_stack import DatabaseStack
from stacks.lambda_stack import LambdaStack
from stacks.secrets_stack import SecretsStack
from stacks.sqs_stack import SqsStack

app = cdk.App()

# Get environment configuration from environment variables or use defaults
aws_account = os.environ.get("CDK_DEFAULT_ACCOUNT")
aws_region = os.environ.get("CDK_DEFAULT_REGION", "ap-southeast-1")

# Define the AWS environment
aws_env = cdk.Environment(account=aws_account, region=aws_region)

# Get stack configuration
environment = os.environ.get("ENVIRONMENT", "dev")
project_name = os.environ.get("PROJECT_NAME", "CtrlAltHeal")

# Create the database stack
database_stack = DatabaseStack(
    app,
    f"{project_name}DatabaseStack",
    env=aws_env,
    environment=environment,
)

# Create the secrets stack
secrets_stack = SecretsStack(
    app,
    f"{project_name}SecretsStack",
    env=aws_env,
    environment=environment,
)

# Create the SQS stack
sqs_stack = SqsStack(
    app,
    f"{project_name}SqsStack",
    env=aws_env,
    environment=environment,
)

# Create the Lambda stack, passing the database, secrets, and SQS stacks
lambda_stack = LambdaStack(
    app,
    f"{project_name}LambdaStack",
    database_stack=database_stack,
    secrets_stack=secrets_stack,
    sqs_stack=sqs_stack,
    env=aws_env,
    environment=environment,
)

# Create the API Gateway stack, passing the Lambda stack
api_gateway_stack = ApiGatewayStack(
    app,
    f"{project_name}ApiGatewayStack",
    lambda_stack=lambda_stack,
    env=aws_env,
    environment=environment,
)

app.synth()
