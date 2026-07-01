"""
マイグレーション 002: users テーブルに password_hash カラムを追加する。

認証機能の追加に伴い、パスワードハッシュを保存するカラムを追加する。
既存ユーザー（シードデータ等）は password_hash = NULL のまま。
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MIGRATION_ID = "002_add_user_password_hash"


def _column_exists(session: Session, table_name: str, column_name: str) -> bool:
    """指定テーブルにカラムが存在するか確認する。"""
    result = session.execute(text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def upgrade(session: Session) -> None:
    """users テーブルに password_hash カラムを追加する。

    冪等性: カラムが既に存在する場合はスキップする。
    既存ユーザーは password_hash = NULL のまま。

    Args:
        session: SQLAlchemy セッション
    """
    if not _column_exists(session, "users", "password_hash"):
        session.execute(
            text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)")
        )
        logger.info("users テーブルに password_hash カラムを追加しました")
    else:
        logger.info("users.password_hash カラムは既に存在します（スキップ）")

    session.commit()
