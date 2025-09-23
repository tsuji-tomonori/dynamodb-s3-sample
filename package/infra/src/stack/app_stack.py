from typing import Any

import aws_cdk as cdk
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
        self.book.table.grant_read_data(self.server.function)

        self.log_bucket = S3Construct(
            self,
            "LogBucket",
        )

        self.server.function.add_environment(
            "LOG_BUCKET_NAME",
            self.log_bucket.bucket.bucket_name,
        )
        self.log_bucket.bucket.grant_read_write(self.server.function)

        self.api = ApigwConstruct(
            self,
            "Api",
            project=project,
            function=self.server.function,  # type: ignore[arg-type]
        )
