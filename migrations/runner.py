"""
愛媛探索AIクイズ - マイグレーションランナー

登録されたマイグレーションを順番に実行する。
各マイグレーションは冪等であり、既に適用済みの変更はスキップされる。
"""

import importlib
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# マイグレーションモジュール名リスト（順番に実行される）
MIGRATION_MODULES = [
    "migrations.001_add_user_xp_level_columns",
    "migrations.002_add_user_password_hash",
    "migrations.003_add_extra_questions",
    "migrations.004_create_bookmarks_table",
    "migrations.005_shuffle_answer_positions",
    "migrations.006_add_user_api_key",
]


def run_migrations(session: Session) -> None:
    """全マイグレーションを順番に実行する。

    各マイグレーションは冪等であるため、繰り返し実行しても安全。

    Args:
        session: SQLAlchemy セッション
    """
    logger.info("マイグレーション実行開始（%d件）", len(MIGRATION_MODULES))

    for module_name in MIGRATION_MODULES:
        logger.info("マイグレーション適用中: %s", module_name)
        try:
            module = importlib.import_module(module_name)
            module.upgrade(session)
            logger.info("マイグレーション完了: %s", module_name)
        except Exception:
            logger.exception("マイグレーション失敗: %s", module_name)
            raise

    logger.info("全マイグレーション完了")
