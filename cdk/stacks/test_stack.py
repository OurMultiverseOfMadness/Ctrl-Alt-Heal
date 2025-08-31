import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    Stack,
)
from constructs import Construct


class TestStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Simple S3 bucket
        bucket = s3.Bucket(
            self,
            "TestBucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        cdk.CfnOutput(
            self,
            "BucketName",
            value=bucket.bucket_name,
            description="Test bucket name",
        )
