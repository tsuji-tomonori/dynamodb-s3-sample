import os

from pydantic import BaseModel, Field


class EnvConfig(BaseModel):
    """環境変数を管理するオブジェクトクラス"""

    model_config = {
        "extra": "ignore",  # 未定義フィールドを無視
        "frozen": True,  # インスタンスを不変にする
        "alias_generator": lambda s: s.upper(),  # フィールド名を大
    }

    books_table_name: str = Field(..., description="BOOKSテーブルの名前")
    log_bucket_name: str = Field(..., description="ログ保存先のS3バケット名")

    @classmethod
    def from_env(cls) -> "EnvConfig":
        """環境変数から設定を読み込む"""
        return cls.model_validate(os.environ)
