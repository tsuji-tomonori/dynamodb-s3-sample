from pathlib import Path
from typing import Any, Self

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
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

        # Add custom policy for CloudWatch Logs with function construct ID
        # Use construct ID instead of function name to avoid circular dependency
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:log-group:/aws/lambda/{construct_id}Function*",
                    f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:log-group:/aws/lambda/{construct_id}Function*:*",
                ],
            )
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

        # Suppress CDK Nag for necessary log stream wildcard permissions on DefaultPolicy
        # Use construct ID pattern matching to avoid circular dependency
        NagSuppressions.add_resource_suppressions_by_path(
            cdk.Stack.of(self),
            f"{self.execution_role.node.path}/DefaultPolicy",
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Lambda function requires wildcard permission for log streams within its specific log group. CloudWatch Logs automatically generates unique stream names with timestamps at runtime, making wildcard necessary. This follows AWS official best practices for Lambda logging and is limited to the specific function's log group.",
                    "appliesTo": [
                        f"Resource::arn:aws:logs:<AWS::Region>:<AWS::AccountId>:log-group:/aws/lambda/{construct_id}Function*",
                        f"Resource::arn:aws:logs:<AWS::Region>:<AWS::AccountId>:log-group:/aws/lambda/{construct_id}Function*:*",
                    ],
                }
            ],
        )

        # Note: Log group is automatically created by Lambda function
        # Manual log group creation removed to avoid circular dependency
        # Lambda will create the log group automatically with default retention
        # If specific retention is needed, it should be set via Lambda function configuration

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


# LogGroup output removed due to circular dependency
# Log group is automatically created by Lambda function
