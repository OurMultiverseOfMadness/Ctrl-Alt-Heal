from aws_cdk import (
    aws_apigateway as apigw,
    aws_logs as logs,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    Stack,
)
from constructs import Construct


class ApiGatewayStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.IVpc,
        alb: elbv2.IApplicationLoadBalancer,
        environment: str = "production",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = environment

        # Create log group for API Gateway
        log_group = logs.LogGroup(
            self,
            "ApiGatewayLogs",
            log_group_name=f"/aws/apigateway/cara-agents-{environment}",
            retention=logs.RetentionDays.ONE_WEEK,
        )

        # Create API Gateway REST API
        api = apigw.RestApi(
            self,
            "CaraAgentsAPI",
            rest_api_name=f"cara-agents-api-{environment}",
            description="API Gateway for Cara-Agents Fargate service",
            deploy_options=apigw.StageOptions(
                stage_name=environment,
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
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
            ),
            cloud_watch_role=True,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                ],
            ),
        )

        # Create integration for ALB using HTTP (not VPC Link)
        alb_integration = apigw.Integration(
            type=apigw.IntegrationType.HTTP_PROXY,
            integration_http_method="ANY",
            options=apigw.IntegrationOptions(
                connection_type=apigw.ConnectionType.INTERNET,
                request_parameters={
                    "integration.request.path.proxy": "method.request.path.proxy",
                },
            ),
            uri=f"http://{alb.load_balancer_dns_name}/{{proxy}}",
        )

        # Add proxy resource to handle all paths
        proxy_resource = api.root.add_resource("{proxy+}")

        # Add methods to proxy resource
        proxy_resource.add_method(
            "GET",
            integration=alb_integration,
            request_parameters={
                "method.request.path.proxy": True,
            },
            authorization_type=apigw.AuthorizationType.NONE,
        )

        proxy_resource.add_method(
            "POST",
            integration=alb_integration,
            request_parameters={
                "method.request.path.proxy": True,
            },
            authorization_type=apigw.AuthorizationType.NONE,
        )

        proxy_resource.add_method(
            "PUT",
            integration=alb_integration,
            request_parameters={
                "method.request.path.proxy": True,
            },
            authorization_type=apigw.AuthorizationType.NONE,
        )

        proxy_resource.add_method(
            "DELETE",
            integration=alb_integration,
            request_parameters={
                "method.request.path.proxy": True,
            },
            authorization_type=apigw.AuthorizationType.NONE,
        )

        # Add root method for health check
        root_integration = apigw.Integration(
            type=apigw.IntegrationType.HTTP_PROXY,
            integration_http_method="GET",
            options=apigw.IntegrationOptions(
                connection_type=apigw.ConnectionType.INTERNET,
            ),
            uri=f"http://{alb.load_balancer_dns_name}/health",
        )

        api.root.add_method(
            "GET",
            integration=root_integration,
            authorization_type=apigw.AuthorizationType.NONE,
        )

        # Output the API Gateway URL
        from aws_cdk import CfnOutput

        CfnOutput(
            self,
            "ApiGatewayURL",
            value=api.url,
            description="API Gateway URL",
        )

        # Output the webhook URL for Telegram
        CfnOutput(
            self,
            "WebhookURL",
            value=f"{api.url}webhook",
            description="Telegram webhook URL (HTTPS)",
        )

        # Store the API for potential use by other stacks
        self.api = api
