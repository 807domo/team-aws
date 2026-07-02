"""
マイグレーション 004: bookmarks テーブルを作成する

ユーザーが問題をブックマーク保存するためのテーブル。
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MIGRATION_ID = "004_create_bookmarks_table"


def _table_exists(session: Session, table_name: str) -> bool:
    """指定テーブルが存在するか確認する。"""
    result = session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    )
    return result.fetchone() is not None


def upgrade(session: Session) -> None:
    """bookmarks テーブルを作成する。

    冪等性: テーブルが既に存在する場合はスキップする。

    Args:
        session: SQLAlchemy セッション
    """
    if not _table_exists(session, "bookmarks"):
        session.execute(
            text("""
                CREATE TABLE bookmarks (
                    id VARCHAR(64) PRIMARY KEY,
                    user_id VARCHAR(64) NOT NULL,
                    question_id VARCHAR(64) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
        )
        logger.info("bookmarks テーブルを作成しました")
    else:
        logger.info("bookmarks テーブルは既に存在します（スキップ）")

    session.commit()
