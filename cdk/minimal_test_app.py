#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.minimal_fargate_stack import MinimalFargateStack

app = cdk.App()

# Get environment configuration from environment variables or use defaults
aws_account = os.environ.get("CDK_DEFAULT_ACCOUNT")
aws_region = os.environ.get("CDK_DEFAULT_REGION", "ap-southeast-1")

# Define the AWS environment
aws_env = cdk.Environment(account=aws_account, region=aws_region)

# Create the minimal Fargate stack
minimal_stack = MinimalFargateStack(
    app,
    "MinimalFargateStack",
    env=aws_env,
)

app.synth()
