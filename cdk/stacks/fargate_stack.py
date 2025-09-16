import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
    Stack,
)
from constructs import Construct

from .database_stack import DatabaseStack
from .secrets_stack import SecretsStack


class FargateStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        database_stack: DatabaseStack,
        secrets_stack: SecretsStack,
        environment: str = "production",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = environment

        # Get the AWS account ID for unique ECR repository naming
        account_id = cdk.Stack.of(self).account

        # Create ECR Repository
        ecr_repository = ecr.Repository(
            self,
            "CaraAgentsECRRepo",
            repository_name=f"cara-agents-{account_id}",
            image_scan_on_push=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        # VPC for Fargate
        vpc = ec2.Vpc(
            self,
            "CtrlAltHealVPC",
            max_azs=2,
        )

        # ECS Cluster
        cluster = ecs.Cluster(
            self,
            "CtrlAltHealCluster",
            vpc=vpc,
        )

        # Security Group for ALB
        alb_security_group = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True,
        )

        # Allow inbound HTTP traffic to ALB
        alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP traffic from anywhere",
        )

        # Security Group for Fargate tasks
        fargate_security_group = ec2.SecurityGroup(
            self,
            "FargateSecurityGroup",
            vpc=vpc,
            description="Security group for Fargate tasks",
            allow_all_outbound=True,
        )

        # Allow inbound traffic from ALB to Fargate tasks
        fargate_security_group.add_ingress_rule(
            peer=alb_security_group,
            connection=ec2.Port.tcp(8000),
            description="Allow traffic from ALB to Fargate tasks",
        )

        # Task Role for the Fargate service
        task_role = iam.Role(
            self,
            "CtrlAltHealTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        # Grant table access to the task role
        database_stack.users_table.grant_read_write_data(task_role)
        database_stack.identities_table.grant_read_write_data(task_role)
        database_stack.conversations_table.grant_read_write_data(task_role)
        database_stack.prescriptions_table.grant_read_write_data(task_role)
        database_stack.fhir_data_table.grant_read_write_data(task_role)

        # Grant S3 bucket access to the task role
        database_stack.uploads_bucket.grant_read_write(task_role)
        database_stack.assets_bucket.grant_read(task_role)

        # Grant access to specific secrets
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    secrets_stack.serper_secret.secret_arn,
                    secrets_stack.telegram_secret.secret_arn,
                ],
            )
        )

        # Grant Bedrock permissions
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],
            )
        )

        # Grant ECR permissions for pulling the image
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=["*"],
            )
        )

        # Task Definition
        task_definition = ecs.FargateTaskDefinition(
            self,
            "CtrlAltHealTaskDef",
            task_role=task_role,
            execution_role=task_role,
            memory_limit_mib=2048,
            cpu=1024,
        )

        # Container - using our ECR image
        container = task_definition.add_container(
            "CtrlAltHealContainer",
            image=ecs.ContainerImage.from_ecr_repository(
                repository=ecr_repository, tag="latest"
            ),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="ctrl-alt-heal",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
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
                "AGENT_VERSION": "4.0",  # Fargate version
            },
            port_mappings=[ecs.PortMapping(container_port=8000)],
        )

        # Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "CaraAgentsALB",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_security_group,
        )

        # Target Group for Fargate tasks
        target_group = elbv2.ApplicationTargetGroup(
            self,
            "CaraAgentsTargetGroup",
            vpc=vpc,
            port=8000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path="/health",
                port="8000",
                protocol=elbv2.Protocol.HTTP,
                healthy_http_codes="200",
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
                timeout=cdk.Duration.seconds(30),
                interval=cdk.Duration.seconds(60),
            ),
        )

        # HTTP Listener
        listener = alb.add_listener(
            "HTTPListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_target_groups=[target_group],
        )

        # Fargate Service
        fargate_service = ecs.FargateService(
            self,
            "CtrlAltHealFargateService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,  # Start with 1 task, auto-scaling will handle scaling up to 2
            assign_public_ip=False,  # No public IP needed with ALB
            security_groups=[fargate_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        # Attach Fargate service to ALB target group
        fargate_service.attach_to_application_target_group(target_group)

        # Auto Scaling Configuration
        # Enable auto-scaling with minimum 1 task for always-on availability
        scaling = fargate_service.auto_scale_task_count(
            min_capacity=1,  # Always keep at least 1 task running
            max_capacity=2,  # Maximum 2 tasks during high load
        )

        # Scale down to 0 after 15 minutes of no activity
        scaling.scale_on_request_count(
            "ScaleOnRequestCount",
            requests_per_target=1,  # Scale up when there's 1 request per target
            scale_in_cooldown=cdk.Duration.minutes(
                15
            ),  # Wait 15 minutes before scaling down
            scale_out_cooldown=cdk.Duration.seconds(
                60
            ),  # Wait 1 minute before scaling up
            target_group=target_group,
        )

        # Output the ALB URL
        cdk.CfnOutput(
            self,
            "ALBURL",
            value=f"http://{alb.load_balancer_dns_name}",
            description="Application Load Balancer URL",
        )

        # Output the webhook URL for Telegram
        cdk.CfnOutput(
            self,
            "WebhookURL",
            value=f"http://{alb.load_balancer_dns_name}/webhook",
            description="Telegram webhook URL",
        )

        # Output ECR repository URI
        cdk.CfnOutput(
            self,
            "ECRRepositoryURI",
            value=ecr_repository.repository_uri,
            description="ECR Repository URI",
        )

        # Store VPC and ALB for use by other stacks
        self.vpc = vpc
        self.alb = alb

        # Export the ALB for use by other stacks
        cdk.CfnOutput(
            self,
            "ALBExport",
            value=alb.load_balancer_arn,
            export_name=f"{self.stack_name}-ALB-ARN",
            description="ALB ARN for use by other stacks",
        )

        # Output ECS service name for deployment script
        cdk.CfnOutput(
            self,
            "ECSServiceName",
            value=fargate_service.service_name,
            description="ECS Service Name for deployment script",
        )

        # Output ECS cluster name for deployment script
        cdk.CfnOutput(
            self,
            "ECSClusterName",
            value=cluster.cluster_name,
            description="ECS Cluster Name for deployment script",
        )
