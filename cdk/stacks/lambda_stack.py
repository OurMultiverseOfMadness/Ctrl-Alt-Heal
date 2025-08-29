import aws_cdk as cdk
from aws_cdk import (
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
    Stack,
)
from constructs import Construct

from .database_stack import DatabaseStack
from .secrets_stack import SecretsStack
from .sqs_stack import SqsStack


class LambdaStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        database_stack: DatabaseStack,
        secrets_stack: SecretsStack,
        sqs_stack: SqsStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda Layer
        layer = _lambda.LayerVersion(
            self,
            "CtrlAltHealLambdaLayer",
            code=_lambda.Code.from_asset("lambda_layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="A layer for Python dependencies",
        )

        # IAM Role for the Worker Lambda
        worker_role = iam.Role(
            self,
            "CtrlAltHealWorkerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Grant table access to the worker role
        database_stack.users_table.grant_read_write_data(worker_role)
        database_stack.identities_table.grant_read_write_data(worker_role)
        database_stack.history_table.grant_read_write_data(worker_role)
        database_stack.prescriptions_table.grant_read_write_data(worker_role)
        database_stack.fhir_table.grant_read_write_data(worker_role)

        # Grant S3 bucket access to the worker role
        database_stack.uploads_bucket.grant_read_write(worker_role)
        database_stack.assets_bucket.grant_read(worker_role)

        # Grant access to specific secrets
        worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    secrets_stack.serper_secret.secret_arn,
                    secrets_stack.telegram_secret.secret_arn,
                ],
            )
        )
        # Grant the Lambda function permissions to invoke the Bedrock model
        worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],
            )
        )

        # Grant the Lambda function permissions to read from the S3 bucket
        worker_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[
                    f"arn:aws:s3:::{database_stack.uploads_bucket.bucket_name}/*"
                ],
            )
        )

        # Grant SQS permissions to the worker role
        sqs_stack.messages_queue.grant_consume_messages(worker_role)

        # Agent Worker Lambda Function
        self.worker_function = _lambda.Function(
            self,
            "CtrlAltHealWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            handler="ctrl_alt_heal.worker.handler",
            code=_lambda.Code.from_asset("../src"),
            role=worker_role,
            layers=[layer],
            environment={
                "USERS_TABLE_NAME": database_stack.users_table.table_name,
                "IDENTITIES_TABLE_NAME": database_stack.identities_table.table_name,
                "HISTORY_TABLE_NAME": database_stack.history_table.table_name,
                "PRESCRIPTIONS_TABLE_NAME": database_stack.prescriptions_table.table_name,
                "FHIR_TABLE_NAME": database_stack.fhir_table.table_name,
                "UPLOADS_BUCKET_NAME": database_stack.uploads_bucket.bucket_name,
                "ASSETS_BUCKET_NAME": database_stack.assets_bucket.bucket_name,
                "SERPER_SECRET_NAME": "ctrl-alt-heal/serper/api-key",
                "TELEGRAM_SECRET_NAME": "ctrl-alt-heal/telegram/bot-token",
                "AGENT_VERSION": "3.2",  # Force a redeployment
            },
            timeout=cdk.Duration.seconds(240),
        )
        self.worker_function.add_event_source(
            lambda_event_sources.SqsEventSource(sqs_stack.messages_queue)
        )

        # IAM Role for the API Handler Lambda
        api_handler_role = iam.Role(
            self,
            "CtrlAltHealApiHandlerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Grant access to secrets for API handler (in case it needs to access them)
        api_handler_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    secrets_stack.serper_secret.secret_arn,
                    secrets_stack.telegram_secret.secret_arn,
                ],
            )
        )

        # Grant SQS permissions to the api handler role
        sqs_stack.messages_queue.grant_send_messages(api_handler_role)

        # API Handler Lambda Function
        self.api_handler_function = _lambda.Function(
            self,
            "CtrlAltHealHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            handler="ctrl_alt_heal.main.handler",
            code=_lambda.Code.from_asset("../src"),
            role=api_handler_role,
            layers=[layer],
            environment={
                "MESSAGES_QUEUE_URL": sqs_stack.messages_queue.queue_url,
            },
            timeout=cdk.Duration.seconds(30),
        )
