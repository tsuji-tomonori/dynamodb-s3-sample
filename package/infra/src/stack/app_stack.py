from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from cdk_nag import NagSuppressions
from constructs import Construct
from src.construct.bucket import S3Construct
from src.construct.function import LambdaConstruct
from src.construct.rest_api import ApigwConstruct
from src.construct.table import DynamoDBConstruct
from src.model.project import Project


class AppStack(cdk.Stack):
    """Unified Application Stack with both Backend and Frontend resources."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        project: Project,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            description=f"{project.description} - Unified Application Stack",
            **kwargs,
        )

        self.server = LambdaConstruct(
            self,
            "Server",
            project=project,
        )

        self.book = DynamoDBConstruct(
            self,
            "Book",
        )

        self.server.function.add_environment(
            "BOOKS_TABLE_NAME",
            self.book.table.table_name,
        )

        assert self.server.function.role is not None, (
            "Lambda function role must be defined"
        )
        self.book.table.grant_read_write_data(self.server.function)

        self.log_bucket = S3Construct(
            self,
            "LogBucket",
        )

        self.server.function.add_environment(
            "LOG_BUCKET_NAME",
            self.log_bucket.bucket.bucket_name,
        )

        # Grant specific S3 permissions instead of wildcard permissions
        self.server.function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                ],
                resources=[
                    f"{self.log_bucket.bucket.bucket_arn}/*",
                ],
            )
        )

        # Suppress CDK Nag for necessary S3 object wildcard permissions
        NagSuppressions.add_resource_suppressions(
            self.server.function.role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Lambda function requires wildcard permission for S3 objects within the specific log bucket. This is necessary for log file operations and follows AWS best practices for Lambda S3 access.",
                    "appliesTo": [
                        "Resource::*/*"
                    ],
                }
            ],
        )

        self.api = ApigwConstruct(
            self,
            "Api",
            project=project,
            function=self.server.function,  # type: ignore[arg-type]
        )
