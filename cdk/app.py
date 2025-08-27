#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.api_gateway_stack import ApiGatewayStack
from stacks.database_stack import DatabaseStack
from stacks.lambda_stack import LambdaStack
from stacks.sqs_stack import SqsStack

app = cdk.App()

# Define the AWS environment
aws_env = cdk.Environment(account="532003627730", region="ap-southeast-1")

# Create the database stack
database_stack = DatabaseStack(
    app,
    "CtrlAltHealDatabaseStack",
    env=aws_env,
)

# Create the SQS stack
sqs_stack = SqsStack(
    app,
    "CtrlAltHealSqsStack",
    env=aws_env,
)

# Create the Lambda stack, passing the database and SQS stacks
lambda_stack = LambdaStack(
    app,
    "CtrlAltHealLambdaStack",
    database_stack=database_stack,
    sqs_stack=sqs_stack,
    env=aws_env,
)

# Create the API Gateway stack, passing the Lambda stack
api_gateway_stack = ApiGatewayStack(
    app,
    "CtrlAltHealApiGatewayStack",
    lambda_stack=lambda_stack,
    env=aws_env,
)

app.synth()
