import datetime

from pynamodb.attributes import (
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.models import Model

from model.book import Book
from model.env import EnvConfig

env = EnvConfig.from_env()


class BookModel(Model):
    class Meta:  # type: ignore
        table_name = env.books_table_name

    # 主キー
    isbn = UnicodeAttribute(hash_key=True)

    # 書籍情報
    title = UnicodeAttribute()
    author = UnicodeAttribute()
    publisher = UnicodeAttribute(null=True)

    # メタデータ
    created_at = UTCDateTimeAttribute(
        default=datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at = UTCDateTimeAttribute(
        default=datetime.datetime.now(datetime.timezone.utc)
    )

    @classmethod
    def from_model(cls, book: Book) -> "BookModel":
        return cls(
            isbn=book.isbn,
            title=book.title,
            author=book.author,
            publisher=book.publisher,
        )
