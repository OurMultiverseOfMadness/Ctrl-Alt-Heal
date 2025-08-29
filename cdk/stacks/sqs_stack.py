import aws_cdk as cdk
from aws_cdk import (
    aws_sqs as sqs,
    Stack,
)
from constructs import Construct


class SqsStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, environment: str = "dev", **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment = environment

        self.messages_queue = sqs.Queue(
            self,
            "MessagesQueue",
            visibility_timeout=cdk.Duration.seconds(300),  # 5 minutes
            retention_period=cdk.Duration.days(4),
        )
