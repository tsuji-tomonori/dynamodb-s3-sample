import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    """pyproject.tomlの[project]セクションの情報を管理するオブジェクトクラス"""

    model_config = {
        "extra": "ignore",  # 未定義フィールドを無視
        "frozen": True,  # インスタンスを不変にする
    }

    name: str = Field(..., description="プロジェクト名")
    version: str = Field(..., description="プロジェクトのバージョン")
    description: str = Field(..., description="プロジェクトの説明")

    @classmethod
    def from_pyproject(
        cls,
        path: Path = Path.cwd() / "pyproject.toml",
    ) -> "ProjectInfo":
        """pyproject.tomlからプロジェクト情報を読み込む"""
        with path.open("rb") as f:
            pyproject = tomllib.load(f)
        project_info = pyproject.get("project", {})
        return cls.model_validate(project_info)
