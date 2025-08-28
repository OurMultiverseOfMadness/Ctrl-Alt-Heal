import aws_cdk as cdk
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    Stack,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for storing user uploads
        self.uploads_bucket = s3.Bucket(
            self,
            "CtrlAltHealUploadsBucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,  # Change in production
            auto_delete_objects=True,  # Change in production
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
        )

        # DynamoDB Table for Users
        self.users_table = self._create_table(
            table_name="ctrl-alt-heal-users", partition_key="user_id"
        )
        self.identities_table = self._create_table(
            table_name="ctrl-alt-heal-identities", partition_key="pk"
        )
        self.history_table = self._create_table(
            table_name="ctrl-alt-heal-history",
            partition_key="user_id",
            sort_key="session_id",
        )
        self.prescriptions_table = self._create_table(
            table_name="ctrl-alt-heal-prescriptions", partition_key="pk", sort_key="sk"
        )
        self.fhir_table = self._create_table(
            table_name="ctrl-alt-heal-fhir", partition_key="pk", sort_key="sk"
        )

    def _create_table(
        self,
        table_name: str,
        partition_key: str,
        sort_key: str | None = None,
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
        )
