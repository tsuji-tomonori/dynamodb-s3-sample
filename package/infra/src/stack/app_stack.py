from typing import Any

import aws_cdk as cdk
from constructs import Construct
from src.model.project import Project
from src.construct.function import LambdaConstruct
from src.construct.rest_api import ApigwConstruct
from src.construct.table import DynamoDBConstruct


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

        self.archive_metadata = DynamoDBConstruct(
            self,
            "ArchiveMetadata",
        )

        self.server.function.add_environment(
            "DYNAMODB_TABLE_NAME",
            self.archive_metadata.table.table_name,
        )

        assert self.server.function.role is not None, (
            "Lambda function role must be defined"
        )
        self.archive_metadata.table.grant_read_data(self.server.function)

        self.api = ApigwConstruct(
            self,
            "Api",
            project=project,
            function=self.server.function,  # type: ignore[arg-type]
        )
