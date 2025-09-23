from pydantic import BaseModel, Field


class Book(BaseModel):
    """書籍情報を管理するオブジェクトクラス"""

    isbn: str = Field(..., description="書籍のISBNコード")
    title: str = Field(..., description="書籍のタイトル")
    author: str = Field(..., description="書籍の著者")
    publisher: str | None = Field(None, description="書籍の出版社")
