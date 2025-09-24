from typing import Any, Self

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class S3Construct(Construct):
    """S3 bucket construct for static hosting and thumbnails."""

    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        enable_access_logging: bool = False,
        access_log_bucket: s3.IBucket | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize S3 construct.

        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            enable_access_logging: Whether to enable server access logging
            access_log_bucket: Bucket to store access logs (for other buckets)
            **kwargs: Additional keyword arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket with optional access logging
        bucket_props = {
            "versioned": True,
            "block_public_access": s3.BlockPublicAccess.BLOCK_ALL,
            "encryption": s3.BucketEncryption.S3_MANAGED,
            "removal_policy": cdk.RemovalPolicy.DESTROY,
        }

        # Add server access logging if enabled and log bucket is provided
        if enable_access_logging and access_log_bucket is not None:
            bucket_props["server_access_logs_bucket"] = access_log_bucket
            bucket_props["server_access_logs_prefix"] = f"access-logs/{construct_id.lower()}/"

        self.bucket = s3.Bucket(
            self,
            "Bucket",
            **bucket_props,
        )

        # Add HTTPS-only policy to enforce SSL
        self.bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="DenyInsecureConnections",
                effect=iam.Effect.DENY,
                principals=[iam.StarPrincipal()],  # type: ignore[arg-type]
                actions=["s3:*"],
                resources=[
                    self.bucket.bucket_arn,
                    f"{self.bucket.bucket_arn}/*",
                ],
                conditions={"Bool": {"aws:SecureTransport": "false"}},
            )
        )

        # Output bucket name
        cdk.CfnOutput(
            self,
            "BucketArn",
            value=self.bucket.bucket_arn,
            description="S3 bucket ARN",
        )
