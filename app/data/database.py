"""
愛媛探索AIクイズ - データベース接続設定

SQLite データベース接続と SessionLocal の定義。
FastAPI 依存性注入用の get_db() ジェネレータを提供する。
DB接続リトライ機構を含む。
"""

import os
import logging
import time
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)

# データベース接続URL（未指定時はSQLiteを使用）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ehime_quiz.db")

# リトライ設定定数
DB_CONNECTION_RETRY_COUNT = 3
DB_CONNECTION_RETRY_DELAY_SECONDS = 1

# エンジン作成（SQLite では check_same_thread=False が必要）
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

# セッションファクトリ
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy ORM のベースクラス"""

    pass


class DatabaseConnectionError(Exception):
    """データベース接続に失敗した際に発生する例外。"""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 依存性注入用のデータベースセッションジェネレータ。

    USE_DYNAMODB=1 の場合はダミーセッション（None）を返す。
    DynamoDBモードではリポジトリが直接DynamoDBを使用するため、
    SQLAlchemyセッションは不要。

    接続失敗時は最大3回リトライし、1秒間隔で再試行する。
    全リトライ失敗時は DatabaseConnectionError を送出する。

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    use_dynamodb = os.environ.get("USE_DYNAMODB", "0") == "1"
    if use_dynamodb:
        yield None  # type: ignore[arg-type]
        return

    last_error: Exception | None = None

    for attempt in range(1, DB_CONNECTION_RETRY_COUNT + 1):
        db: Session | None = None
        try:
            db = SessionLocal()
            yield db
            return
        except OperationalError as e:
            last_error = e
            logger.warning(
                "DB接続試行 %d/%d 失敗: %s",
                attempt,
                DB_CONNECTION_RETRY_COUNT,
                str(e),
            )
            if attempt < DB_CONNECTION_RETRY_COUNT:
                time.sleep(DB_CONNECTION_RETRY_DELAY_SECONDS)
        finally:
            if db is not None:
                db.close()

    # 全リトライ失敗
    raise DatabaseConnectionError(
        f"データベース接続に失敗しました（{DB_CONNECTION_RETRY_COUNT}回試行）: {last_error}"
    )


def create_tables() -> None:
    """
    全テーブルを作成する（存在しない場合のみ）。

    アプリケーション起動時に呼び出す。
    """
    Base.metadata.create_all(bind=engine)
