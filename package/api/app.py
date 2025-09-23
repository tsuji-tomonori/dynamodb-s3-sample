from fastapi import FastAPI

from model import env
from model.pyproject import ProjectInfo
from router.books import router as books_router

# pyproject.tomlからプロジェクト情報を読み込む
project_info = ProjectInfo.from_pyproject()

# 環境変数の取得
env = env.EnvConfig.from_env()


# FastAPIアプリケーションのインスタンス化
app = FastAPI(
    title=project_info.name,
    version=project_info.version,
    description=project_info.description,
    docs_url="/docs",
    openapi_prefix=f"/{env.project_major_version}/",  # バージョニング対応
)

# ルーターの登録
app.include_router(
    prefix="/books",
    tags=["Books"],
    router=books_router,
)


@app.get("/health", tags=["Health"])
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}
