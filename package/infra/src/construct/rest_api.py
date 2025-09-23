from typing import Any, Self

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from cdk_nag import NagSuppressions
from constructs import Construct
from src.model.project import Project


class ApigwConstruct(Construct):
    """API Gateway construct for FastAPI backend."""

    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        project: Project,
        function: lambda_.IFunction,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize API Gateway construct.

        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            environment: Environment name (dev/prod)
            **kwargs: Additional keyword arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create custom CloudWatch role for API Gateway instead of AWS managed policy
        self.cloudwatch_role = iam.Role(
            self,
            "CloudWatchRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="Custom API Gateway CloudWatch logs role",
        )


        # Create API Gateway without default CloudWatch role
        self.api_gateway = apigw.LambdaRestApi(
            self,
            "LambdaRestApi",
            handler=function,
            proxy=True,
            description=project.description,
            cloud_watch_role=False,  # Disable default CloudWatch role creation
            deploy_options=apigw.StageOptions(
                logging_level=apigw.MethodLoggingLevel.ERROR,
                stage_name=project.major_version,
            ),
        )

        # Add specific CloudWatch permissions after API Gateway is created
        self.cloudwatch_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                    "logs:PutLogEvents",
                    "logs:GetLogEvents",
                    "logs:FilterLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:log-group:API-Gateway-Execution-Logs_{self.api_gateway.rest_api_id}/{project.major_version}",
                    f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:log-group:API-Gateway-Execution-Logs_{self.api_gateway.rest_api_id}/{project.major_version}:*",
                ],
            )
        )

        # Set the CloudWatch role at account level for API Gateway
        apigw.CfnAccount(
            self,
            "CloudWatchAccount",
            cloud_watch_role_arn=self.cloudwatch_role.role_arn,
        )

        # Suppress CDK Nag for necessary API Gateway log stream wildcard permissions
        NagSuppressions.add_resource_suppressions(
            self.cloudwatch_role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "API Gateway requires wildcard permission for log streams within its specific log group. This is necessary for API Gateway access logging and follows AWS best practices.",
                    "appliesTo": [
                        "Resource::arn:aws:logs:*:*:log-group:API-Gateway-Execution-Logs_*/*:*"
                    ],
                }
            ],
        )

        # Output API Gateway URL
        cdk.CfnOutput(
            self,
            "ApiGatewayUrl",
            value=self.api_gateway.url,
            description="API Gateway URL",
        )

        cdk.CfnOutput(
            self,
            "ApigwLogGroupName",
            value=f"API-Gateway-Execution-Logs_{self.api_gateway.rest_api_id}/{self.api_gateway.deployment_stage.stage_name}",
            description="API Gateway log group name",
        )
