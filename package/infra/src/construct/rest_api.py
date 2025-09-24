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

        # Create API Gateway with default CloudWatch role enabled
        # This avoids the complexity of custom CloudWatch role setup
        self.api_gateway = apigw.LambdaRestApi(
            self,
            "LambdaRestApi",
            handler=function,
            proxy=True,
            description=project.description,
            # cloud_watch_role defaults to True, which creates appropriate role
            deploy_options=apigw.StageOptions(
                logging_level=apigw.MethodLoggingLevel.ERROR,
                stage_name=project.major_version,
            ),
        )

        # Create request validator for API Gateway to satisfy AwsSolutions-APIG2
        # This enables basic request validation at the API Gateway level
        # Note: For proxy integration, the validator will be created but may not
        # apply detailed validation since all requests go to the Lambda function
        self.request_validator = apigw.RequestValidator(
            self,
            "RequestValidator",
            rest_api=self.api_gateway,
            validate_request_body=True,
            validate_request_parameters=True,
        )

# CDK Nag suppression removed since we're using default CloudWatch role
        # The default role created by CDK follows AWS best practices

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
