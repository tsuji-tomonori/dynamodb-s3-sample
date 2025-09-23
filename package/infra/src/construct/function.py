from pathlib import Path
from typing import Any, Self

import aws_cdk as cdk
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs
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

        # Create Lambda function
        self.function = lambda_.Function(
            self,
            "Function",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="main.handler",
            code=lambda_.Code.from_asset("../api"),
            memory_size=5192,
            timeout=cdk.Duration.seconds(15),
            layers=[
                self.dependencies_layer,
            ],
            logging_format=lambda_.LoggingFormat.JSON,
            system_log_level_v2=lambda_.SystemLogLevel.WARN,
            application_log_level_v2=lambda_.ApplicationLogLevel.WARN,
            description=project.description,
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
