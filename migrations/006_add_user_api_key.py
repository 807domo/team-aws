"""
マイグレーション006: ユーザーテーブルにGemini APIキーカラムを追加

ユーザーごとにAPIキーを保存可能にする。
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def upgrade(session: Session) -> None:
    """usersテーブルにgemini_api_keyカラムを追加する（冪等）。"""
    try:
        session.execute(text(
            "ALTER TABLE users ADD COLUMN gemini_api_key TEXT DEFAULT NULL"
        ))
        session.commit()
        logger.info("gemini_api_key カラムを追加しました")
    except Exception as e:
        session.rollback()
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            logger.info("gemini_api_key カラムは既に存在します")
        else:
            logger.info("gemini_api_key カラム追加スキップ: %s", str(e))
