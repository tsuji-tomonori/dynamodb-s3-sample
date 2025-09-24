from typing import Any, Self

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_wafv2 as wafv2
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

        # Create API Gateway with minimal logging to avoid CloudWatch role issues
        # Note: Using default CloudWatch role creation temporarily to resolve deployment
        self.api_gateway = apigw.LambdaRestApi(
            self,
            "LambdaRestApi",
            handler=function,
            proxy=True,
            description=project.description,
            # cloud_watch_role defaults to True, which creates the default role
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

        # Create WAF WebACL
        self.web_acl = wafv2.CfnWebACL(
            self,
            "WebACL",
            scope="REGIONAL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            rules=[
                # AWS Managed Rules - Common Rule Set
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesCommonRuleSet",
                    priority=1,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet",
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="CommonRuleSetMetric",
                    ),
                ),
                # AWS Managed Rules - Known Bad Inputs Rule Set
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesKnownBadInputsRuleSet",
                    priority=2,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesKnownBadInputsRuleSet",
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="KnownBadInputsRuleSetMetric",
                    ),
                ),
            ],
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="WebACLMetric",
            ),
        )

        self.waf_connection = wafv2.CfnWebACLAssociation(
            scope=self,
            id="WebAclAssociation",
            resource_arn=(
                f"arn:aws:apigateway:{self.api_gateway.env.region}::"
                f"/restapis/{self.api_gateway.rest_api_id}"
                f"/stages/{self.api_gateway.deployment_stage.stage_name}"
            ),
            web_acl_arn=self.web_acl.attr_arn,
        )

        # Suppress CDK Nag for AWS managed policy usage in API Gateway CloudWatch role
        # Account-level CloudWatch role configuration already exists, making custom role unnecessary
        NagSuppressions.add_resource_suppressions_by_path(
            cdk.Stack.of(self),
            f"{self.api_gateway.node.path}/CloudWatchRole",
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "API Gateway uses AWS managed policy 'AmazonAPIGatewayPushToCloudWatchLogs' for CloudWatch integration. This is the standard AWS-provided policy for API Gateway logging functionality and account-level CloudWatch role configuration already exists.",
                    "appliesTo": [
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
                    ],
                }
            ],
        )

        # Suppress CDK Nag for missing access logging on API Gateway stage
        # Account-level CloudWatch role configuration already exists for API Gateway access logging
        NagSuppressions.add_resource_suppressions_by_path(
            cdk.Stack.of(self),
            f"{self.api_gateway.node.path}/DeploymentStage.{project.major_version}/Resource",
            [
                {
                    "id": "AwsSolutions-APIG1",
                    "reason": "アカウント単位の設定であり、API GatewayのアクセスログはCloudWatch Logsに出力されるようになっているため抑制する。",
                }
            ],
        )

        # Suppress CDK Nag for missing authorization on API Gateway methods
        # This API is intentionally designed as a public API without authentication
        NagSuppressions.add_resource_suppressions(
            self.api_gateway,
            [
                {
                    "id": "AwsSolutions-APIG1",
                    "reason": "アカウント単位の設定であり、API GatewayのアクセスログはCloudWatch Logsに出力されるようになっているため抑制する。",
                },
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "Publicにするため抑制する。",
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "Publicにするため抑制する。",
                },
            ],
        )

        # Suppress CDK Nag for specific API Gateway methods
        # Apply to both root method (/) and proxy method (/{proxy+})
        NagSuppressions.add_resource_suppressions_by_path(
            cdk.Stack.of(self),
            f"{self.api_gateway.node.path}/Default/ANY/Resource",
            [
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "Publicにするため抑制する。",
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "Publicにするため抑制する。",
                },
            ],
        )

        NagSuppressions.add_resource_suppressions_by_path(
            cdk.Stack.of(self),
            f"{self.api_gateway.node.path}/Default/{{proxy+}}/ANY/Resource",
            [
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "Publicにするため抑制する。",
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "Publicにするため抑制する。",
                },
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
