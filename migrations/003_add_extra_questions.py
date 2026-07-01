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
    # 既に投入済みかチェック（最初の追加問題ID）
    result = session.execute(
        text("SELECT COUNT(*) FROM questions WHERE id = 'q-bp-013'")
    )
    count = result.scalar()
    if count > 0:
        logger.info("追加問題は既に投入済みです（スキップ）")
        return

    from app.data.models import QuestionModel
    from app.data.seed_data_extra import EXTRA_QUESTIONS, EXTRA_QUESTIONS_2

    for question_data in EXTRA_QUESTIONS + EXTRA_QUESTIONS_2:
        question = QuestionModel(
            id=question_data["id"],
            course_id=question_data["course_id"],
            text=question_data["text"],
            choice_1=question_data["choice_1"],
            choice_2=question_data["choice_2"],
            choice_3=question_data["choice_3"],
            choice_4=question_data["choice_4"],
            correct_choice_index=question_data["correct_choice_index"],
            ehime_trivia=question_data["ehime_trivia"],
            aws_ai_explanation=question_data["aws_ai_explanation"],
            difficulty=question_data["difficulty"],
            exam_domain=question_data["exam_domain"],
        )
        session.add(question)

    session.commit()
    logger.info("追加問題を投入しました（26問）")
