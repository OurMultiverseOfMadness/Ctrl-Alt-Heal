from aws_cdk import (
    aws_apigateway as apigw,
    aws_logs as logs,
    Stack,
)
from constructs import Construct

from .lambda_stack import LambdaStack


class ApiGatewayStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        lambda_stack: LambdaStack,
        environment: str = "dev",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = environment

        log_group = logs.LogGroup(self, "ApiAccessLogs")

        api = apigw.LambdaRestApi(
            self,
            "Api",
            handler=lambda_stack.webhook_function,
            proxy=False,
            deploy_options=apigw.StageOptions(
                access_log_destination=apigw.LogGroupLogDestination(log_group),
                access_log_format=apigw.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True,
                ),
            ),
            cloud_watch_role=True,
        )

        # Create the Lambda integration for webhook handler
        webhook_integration = apigw.LambdaIntegration(lambda_stack.webhook_function)

        items = api.root.add_resource("webhook")
        items.add_method("POST", webhook_integration, api_key_required=False)
