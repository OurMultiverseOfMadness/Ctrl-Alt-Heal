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
        environment: str = "dev",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = environment

        # Lambda Layer for dependencies (following official strands-agents approach)
        dependencies_layer = _lambda.LayerVersion(
            self,
            "DependenciesLayerV2",
            code=_lambda.Code.from_asset("../packaging/dependencies.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Dependencies needed for agent-based lambda",
        )

        # IAM Role for the Worker Lambda
        worker_role = iam.Role(
            self,
            "WorkerRole",
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
        database_stack.conversations_table.grant_read_write_data(worker_role)
        database_stack.prescriptions_table.grant_read_write_data(worker_role)
        database_stack.fhir_data_table.grant_read_write_data(worker_role)

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
        # Grant SQS send permissions for the webhook handler
        sqs_stack.messages_queue.grant_send_messages(worker_role)

        # Webhook Handler Lambda Function (for Telegram webhook)
        self.webhook_function = _lambda.Function(
            self,
            "WebhookHandler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="ctrl_alt_heal.main.handler",
            code=_lambda.Code.from_asset("../packaging/app.zip"),
            role=worker_role,  # Reuse the same role
            layers=[dependencies_layer],
            environment={
                "MESSAGES_QUEUE_URL": sqs_stack.messages_queue.queue_url,
                "ENVIRONMENT": environment,
            },
            timeout=cdk.Duration.seconds(30),
        )

        # Agent Worker Lambda Function (following official strands-agents approach)
        self.worker_function = _lambda.Function(
            self,
            "Worker",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="ctrl_alt_heal.worker.handler",
            code=_lambda.Code.from_asset("../packaging/app.zip"),
            role=worker_role,
            layers=[dependencies_layer],
            environment={
                "USERS_TABLE_NAME": database_stack.users_table.table_name,
                "IDENTITIES_TABLE_NAME": database_stack.identities_table.table_name,
                "CONVERSATIONS_TABLE_NAME": database_stack.conversations_table.table_name,
                "PRESCRIPTIONS_TABLE_NAME": database_stack.prescriptions_table.table_name,
                "FHIR_DATA_TABLE_NAME": database_stack.fhir_data_table.table_name,
                "UPLOADS_BUCKET_NAME": database_stack.uploads_bucket.bucket_name,
                "ASSETS_BUCKET_NAME": database_stack.assets_bucket.bucket_name,
                "SERPER_SECRET_NAME": f"ctrl-alt-heal/{environment}/serper/api-key",
                "TELEGRAM_SECRET_NAME": f"ctrl-alt-heal/{environment}/telegram/bot-token",
                "ENVIRONMENT": environment,
                "AGENT_VERSION": "3.6",  # Force a redeployment
                # Disable OpenTelemetry telemetry collection to prevent Lambda compatibility issues
                "OTEL_TRACES_SAMPLER": "off",
                "OTEL_METRICS_EXPORTER": "none",
                "OTEL_LOGS_EXPORTER": "none",
                "OTEL_PYTHON_DISABLED": "true",
                "OTEL_PYTHON_TRACER_PROVIDER": "none",
                "OTEL_PYTHON_METER_PROVIDER": "none",
                "OTEL_PYTHON_LOGGER_PROVIDER": "none",
            },
            timeout=cdk.Duration.seconds(240),
        )
        self.worker_function.add_event_source(
            lambda_event_sources.SqsEventSource(sqs_stack.messages_queue)
        )
