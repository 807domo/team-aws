"""
マイグレーション 003: 模擬試験65問確保のための追加問題を投入する。

既に投入済みの場合はスキップする（冪等性を確保）。
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MIGRATION_ID = "003_add_extra_questions"


def upgrade(session: Session) -> None:
    """追加問題を投入する。

    冪等性: 最初の追加問題IDが既に存在する場合はスキップする。

    Args:
        session: SQLAlchemy セッション
    """
    # このマイグレーションは不要（seed_database()が全問題を一括投入するため）
    logger.info("003_add_extra_questions: スキップ（seed_database()で一括投入済み）")
