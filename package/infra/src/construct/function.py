from pathlib import Path
from typing import Any, Self

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs
from cdk_nag import NagSuppressions
from constructs import Construct
from src.model.project import Project


class LambdaConstruct(Construct):
    """Lambda function construct for FastAPI backend."""

    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        project: Project,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize Lambda construct.

        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            project: Project metadata
            **kwargs: Additional keyword arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create custom execution role to replace AWS managed policy
        self.execution_role = iam.Role(
            self,
            "ExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),  # type: ignore
            description="Custom Lambda execution role with minimal permissions",
        )

        # Create Lambda layer for dependencies
        layer_path = str(Path(__file__).resolve().parents[4] / ".layers")
        self.dependencies_layer = lambda_.LayerVersion(
            self,
            "LayerVersion",
            code=lambda_.Code.from_asset(
                layer_path,
                exclude=[
                    "**/__pycache__",
                    "**/*.pyc",
                ],
            ),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
            description=project.description,
        )

        # Create Lambda function with custom role
        self.function = lambda_.Function(
            self,
            "Function",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="main.handler",
            code=lambda_.Code.from_asset("../api"),
            memory_size=5192,
            timeout=cdk.Duration.seconds(15),
            role=self.execution_role,  # type: ignore
            layers=[
                self.dependencies_layer,
            ],
            logging_format=lambda_.LoggingFormat.JSON,
            system_log_level_v2=lambda_.SystemLogLevel.WARN,
            application_log_level_v2=lambda_.ApplicationLogLevel.WARN,
            description=project.description,
            environment={
                "PROJECT_NAME": project.name,
                "PROJECT_MAJOR_VERSION": project.major_version,
                "PROJECT_SEMANTIC_VERSION": project.semantic_version,
            },
        )

        # Add custom policy for CloudWatch Logs with specific function name
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:log-group:/aws/lambda/{self.function.function_name}",
                    f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:log-group:/aws/lambda/{self.function.function_name}:*",
                ],
            )
        )

        # Suppress CDK Nag for necessary log stream wildcard permissions on DefaultPolicy
        NagSuppressions.add_resource_suppressions_by_path(
            cdk.Stack.of(self),
            f"{self.execution_role.node.path}/DefaultPolicy",
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Lambda function requires wildcard permission for log streams within its specific log group. CloudWatch Logs automatically generates unique stream names with timestamps at runtime, making wildcard necessary. This follows AWS official best practices for Lambda logging and is limited to the specific function's log group.",
                    "appliesTo": [
                        "Resource::arn:aws:logs:<AWS::Region>:<AWS::AccountId>:log-group:/aws/lambda/<ServerFunctionB9E3FD9F>:*"
                    ],
                }
            ],
        )

        # Create log group with retention
        self.log_group = aws_logs.LogGroup(
            self,
            "LogGroup",
            log_group_name=f"/aws/lambda/{self.function.function_name}",
            retention=aws_logs.RetentionDays.ONE_MONTH,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Output function ARN
        cdk.CfnOutput(
            self,
            "FunctionArn",
            value=self.function.function_arn,
            description="Lambda function ARN",
        )

        cdk.CfnOutput(
            self,
            "DependenciesLayerArn",
            value=self.dependencies_layer.layer_version_arn,
            description="Lambda dependencies layer ARN",
        )

        cdk.CfnOutput(
            self,
            "LogGroupArn",
            value=self.log_group.log_group_arn,
            description="Log group ARN",
        )
