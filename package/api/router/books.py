import uuid

from fastapi import APIRouter

from core.s3 import save_log_to_s3
from db.book import BookModel
from model.book import Book
from model.log import AccessLog

router = APIRouter()


@router.post("", summary="ISBN書籍登録")
async def create_book(book: Book) -> int:
    """書籍を登録するエンドポイント"""
    BookModel.from_model(book).save()
    save_log_to_s3(
        AccessLog(
            request_id=str(uuid.uuid4()),
            event=f"Book with ISBN {book.isbn} created",
        )
    )
    return 201


@router.get("/{isbn}", summary="書籍情報取得")
async def get_book(isbn: str) -> Book:
    """書籍情報を取得するエンドポイント"""
    book = BookModel.get(isbn)
    save_log_to_s3(
        AccessLog(
            request_id=str(uuid.uuid4()),
            event=f"Book with ISBN {isbn} retrieved",
        )
    )
    return Book(
        isbn=book.isbn,
        title=book.title,
        author=book.author,
        publisher=book.publisher,
    )


@router.delete("/{isbn}", summary="書籍削除")
async def delete_book(isbn: str) -> int:
    """書籍を削除するエンドポイント"""
    BookModel.get(isbn).delete()
    save_log_to_s3(
        AccessLog(
            request_id=str(uuid.uuid4()),
            event=f"Book with ISBN {isbn} deleted",
        )
    )
    return 204
