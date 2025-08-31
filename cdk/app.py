#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.database_stack import DatabaseStack
from stacks.fargate_stack import FargateStack
from stacks.secrets_stack import SecretsStack
from stacks.api_gateway_stack import ApiGatewayStack

app = cdk.App()

# Get environment configuration from environment variables or use defaults
aws_account = os.environ.get("CDK_DEFAULT_ACCOUNT")
aws_region = os.environ.get("CDK_DEFAULT_REGION", "ap-southeast-1")

# Define the AWS environment
aws_env = cdk.Environment(account=aws_account, region=aws_region)

# Get stack configuration
environment = os.environ.get("ENVIRONMENT", "production")
project_name = os.environ.get("PROJECT_NAME", "Cara-Agents")

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

# Create the Fargate stack, passing the database and secrets stacks
fargate_stack = FargateStack(
    app,
    f"{project_name}FargateStack",
    database_stack=database_stack,
    secrets_stack=secrets_stack,
    env=aws_env,
    environment=environment,
)

# Create the API Gateway stack, passing the VPC and ALB from Fargate stack
api_gateway_stack = ApiGatewayStack(
    app,
    f"{project_name}ApiGatewayStack",
    vpc=fargate_stack.vpc,
    alb=fargate_stack.alb,
    env=aws_env,
    environment=environment,
)

# Add dependency to ensure Fargate stack is deployed before API Gateway
api_gateway_stack.add_dependency(fargate_stack)

app.synth()
