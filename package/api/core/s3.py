import datetime
import json
import logging

import boto3

from model.env import EnvConfig
from model.log import AccessLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = EnvConfig.from_env()
s3_client = boto3.client("s3")
bucket_name = env.log_bucket_name
s3_resource = boto3.resource("s3")
bucket = s3_resource.Bucket(bucket_name)


def save_log_to_s3(log: AccessLog) -> None:
    """ログ情報をS3に保存する関数

    Args:
        log (AccessLog): 保存するログ情報のオブジェクト
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d/%H%M%S")
    request_id = log.request_id
    object_key = f"logs/{timestamp}_{request_id}.json"

    try:
        bucket.put_object(
            Key=object_key,
            Body=json.dumps(log.model_dump(), ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )
        logger.info(f"Log saved to S3: s3://{bucket_name}/{object_key}")
    except Exception:
        logger.exception(
            f"Unexpected error occurred while saving log to S3. request_id={request_id}"
        )
