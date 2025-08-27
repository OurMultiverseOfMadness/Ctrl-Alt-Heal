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
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        log_group = logs.LogGroup(self, "CtrlAltHealApiAccessLogs")

        api = apigw.LambdaRestApi(
            self,
            "CtrlAltHealApi",
            handler=lambda_stack.api_handler_function,
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

        # Create the Lambda integration
        webhook_integration = apigw.LambdaIntegration(lambda_stack.api_handler_function)

        items = api.root.add_resource("webhook")
        items.add_method("POST", webhook_integration, api_key_required=False)
