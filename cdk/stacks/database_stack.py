import aws_cdk as cdk
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    Stack,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, environment: str = "dev", **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = environment
        self.table_prefix = f"ctrl-alt-heal-{environment}"

        # Get the AWS account ID for unique bucket naming
        account_id = cdk.Stack.of(self).account

        # S3 bucket for storing user uploads
        self.uploads_bucket = s3.Bucket(
            self,
            "UploadsBucket",
            bucket_name=f"{self.table_prefix}-user-uploads-{account_id}",
            removal_policy=cdk.RemovalPolicy.DESTROY,  # Change in production
            auto_delete_objects=True,  # Change in production
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
        )

        self.assets_bucket = s3.Bucket(
            self,
            "AssetsBucket",
            bucket_name=f"{self.table_prefix}-system-assets-{account_id}",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
            versioned=True,  # Enable versioning for the system prompt
        )

        # Deploy the system prompt to the assets bucket
        s3_deployment.BucketDeployment(
            self,
            "DeploySystemPrompt",
            sources=[s3_deployment.Source.asset("../src/ctrl_alt_heal/agent")],
            destination_bucket=self.assets_bucket,
            # We only want to deploy the system_prompt.txt file
            include=["system_prompt.txt"],
        )

        # DynamoDB Tables with improved naming and structure
        self.users_table = self._create_table(
            table_name=f"{self.table_prefix}_user_profiles",
            partition_key="user_id",
            description="User profiles and preferences",
        )

        self.identities_table = self._create_table(
            table_name=f"{self.table_prefix}_external_identities",
            partition_key="identity_key",
            description="External identity provider mappings (Telegram, etc.)",
        )

        self.conversations_table = self._create_table(
            table_name=f"{self.table_prefix}_conversation_history",
            partition_key="user_id",
            sort_key="session_id",
            description="Conversation history and session management",
        )

        self.prescriptions_table = self._create_table(
            table_name=f"{self.table_prefix}_medical_prescriptions",
            partition_key="user_id",
            sort_key="prescription_id",
            description="Medical prescriptions and medication information",
        )

        self.fhir_data_table = self._create_table(
            table_name=f"{self.table_prefix}_fhir_resources",
            partition_key="user_id",
            sort_key="resource_id",
            description="FHIR-compliant healthcare data resources",
        )

    def _create_table(
        self,
        table_name: str,
        partition_key: str,
        sort_key: str | None = None,
        description: str | None = None,
    ) -> dynamodb.Table:
        pk = dynamodb.Attribute(name=partition_key, type=dynamodb.AttributeType.STRING)
        sk = (
            dynamodb.Attribute(name=sort_key, type=dynamodb.AttributeType.STRING)
            if sort_key
            else None
        )
        return dynamodb.Table(
            self,
            table_name,
            table_name=table_name,
            partition_key=pk,
            sort_key=sk,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,  # Change for production
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),  # Enable PITR for data protection
            contributor_insights_enabled=True,  # Enable contributor insights for monitoring
        )
