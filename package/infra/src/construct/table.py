from typing import Any, Self

import aws_cdk as cdk
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class DynamoDBConstruct(Construct):
    """DynamoDB table construct for archive metadata."""

    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize DynamoDB construct.

        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            **kwargs: Additional keyword arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB table
        self.table = dynamodb.Table(
            self,
            "Table",
            partition_key=dynamodb.Attribute(
                name="isbn",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Output table name
        cdk.CfnOutput(
            self,
            "TableArn",
            value=self.table.table_arn,
            description="DynamoDB table ARN",
        )
