"""
マイグレーション 001: users テーブルに total_xp, level カラムを追加する

既存ユーザーはデフォルト値（total_xp=0, level=1）で初期化される。
SQLite の ALTER TABLE は1ステートメントにつき1カラムのみ追加可能。

Requirements: 9.3
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MIGRATION_ID = "001_add_user_xp_level_columns"


def _column_exists(session: Session, table_name: str, column_name: str) -> bool:
    """指定テーブルにカラムが存在するか確認する。"""
    result = session.execute(text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def upgrade(session: Session) -> None:
    """users テーブルに total_xp と level カラムを追加する。

    冪等性: カラムが既に存在する場合はスキップする。
    既存ユーザーはデフォルト値で初期化される。

    Args:
        session: SQLAlchemy セッション
    """
    if not _column_exists(session, "users", "total_xp"):
        session.execute(
            text("ALTER TABLE users ADD COLUMN total_xp INTEGER NOT NULL DEFAULT 0;")
        )
        logger.info("users テーブルに total_xp カラムを追加しました")
    else:
        logger.info("users.total_xp カラムは既に存在します（スキップ）")

    if not _column_exists(session, "users", "level"):
        session.execute(
            text("ALTER TABLE users ADD COLUMN level INTEGER NOT NULL DEFAULT 1;")
        )
        logger.info("users テーブルに level カラムを追加しました")
    else:
        logger.info("users.level カラムは既に存在します（スキップ）")

    session.commit()
