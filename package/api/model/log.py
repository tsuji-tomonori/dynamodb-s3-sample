import datetime

from pydantic import BaseModel, Field


class AccessLog(BaseModel):
    """基本的なログ情報を管理するオブジェクトクラス"""

    timestamp: str = Field(
        default=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        description="ログのタイムスタンプ",
    )
    request_id: str = Field(..., description="リクエストID")
    event: str = Field(..., description="イベントの内容")
