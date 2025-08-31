import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_logs as logs,
    Stack,
)
from constructs import Construct


class MinimalFargateStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC for Fargate
        vpc = ec2.Vpc(
            self,
            "MinimalVPC",
            max_azs=2,
        )

        # ECS Cluster
        cluster = ecs.Cluster(
            self,
            "MinimalCluster",
            vpc=vpc,
        )

        # Task Role for the Fargate service
        task_role = iam.Role(
            self,
            "MinimalTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        # Task Definition
        task_definition = ecs.FargateTaskDefinition(
            self,
            "MinimalTaskDef",
            task_role=task_role,
            execution_role=task_role,
            memory_limit_mib=512,
            cpu=256,
        )

        # Container - using a public image instead of local asset
        container = task_definition.add_container(
            "MinimalContainer",
            image=ecs.ContainerImage.from_registry("nginx:alpine"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="minimal-test",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment={
                "TEST_ENV": "minimal",
            },
            port_mappings=[ecs.PortMapping(container_port=80)],
        )

        # Fargate Service
        fargate_service = ecs.FargateService(
            self,
            "MinimalFargateService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            assign_public_ip=True,
        )

        # Output
        cdk.CfnOutput(
            self,
            "ServiceName",
            value=fargate_service.service_name,
            description="Minimal Fargate service name",
        )
