from typing import Any, Self

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda as lambda_
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

        # Create API Gateway
        self.api_gateway = apigw.LambdaRestApi(
            self,
            "LambdaRestApi",
            handler=function,
            proxy=True,
            description=project.description,
            deploy_options=apigw.StageOptions(
                logging_level=apigw.MethodLoggingLevel.ERROR,
                stage_name=project.major_version,
            ),
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
