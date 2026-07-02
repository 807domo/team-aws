"""
愛媛探索AIクイズ - Question Repository

問題データの永続化とクエリを担当するリポジトリクラス。
SQLAlchemy Session を使用してデータベースアクセスを行う。
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.data.models import QuestionModel
from app.domain.models import Difficulty, Question
from app.domain.question_validator import validate_question


class QuestionRepository:
    """問題データの永続化・取得を行うリポジトリ"""

    def __init__(self, session: Session) -> None:
        """
        Args:
            session: SQLAlchemy データベースセッション
        """
        self._session = session

    def create_question(self, question_data: dict) -> Question:
        """
        問題を作成して永続化する。

        バリデーションを実行し、不正データはリジェクトする。
        question_data に id が含まれない場合は UUID を自動生成する。

        Args:
            question_data: 問題データ辞書

        Returns:
            作成された Question ドメインオブジェクト

        Raises:
            ValueError: バリデーション失敗時（エラーリスト付き）
        """
        # ID が未指定の場合は UUID を生成（バリデーション前に設定）
        if not question_data.get("id"):
            question_data = {**question_data, "id": str(uuid.uuid4())}

        # バリデーション実行
        result = validate_question(question_data)
        if not result.is_valid:
            raise ValueError(f"問題データが不正です: {result.errors}")

        question_id = question_data["id"]

        # SQLAlchemy モデルを作成
        model = QuestionModel(
            id=question_id,
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
            exam_domain=question_data.get("exam_domain", ""),
        )

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)

        return self._to_domain(model)

    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """
        ID を指定して問題を取得する。

        Args:
            question_id: 問題の一意識別子

        Returns:
            Question ドメインオブジェクト。見つからない場合は None。
        """
        model = (
            self._session.query(QuestionModel)
            .filter(QuestionModel.id == question_id)
            .first()
        )
        if model is None:
            return None
        return self._to_domain(model)

    def get_questions_by_course(self, course_id: str) -> list[Question]:
        """
        コース ID を指定して問題一覧を取得する。

        Args:
            course_id: コースの一意識別子

        Returns:
            該当コースの Question リスト
        """
        models = (
            self._session.query(QuestionModel)
            .filter(QuestionModel.course_id == course_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_questions_by_domain(self, domain: str) -> list[Question]:
        """
        試験ドメインを指定して問題一覧を取得する。

        Args:
            domain: 試験ドメイン名（例: "Cloud Concepts", "Security"）

        Returns:
            該当ドメインの Question リスト
        """
        models = (
            self._session.query(QuestionModel)
            .filter(QuestionModel.exam_domain == domain)
            .all()
        )
        return [self._to_domain(m) for m in models]

    @staticmethod
    def _to_domain(model: QuestionModel) -> Question:
        """
        SQLAlchemy モデルをドメイン Question dataclass に変換する。

        Args:
            model: QuestionModel インスタンス

        Returns:
            Question ドメインオブジェクト
        """
        return Question(
            id=model.id,
            course_id=model.course_id,
            text=model.text,
            choice_1=model.choice_1,
            choice_2=model.choice_2,
            choice_3=model.choice_3,
            choice_4=model.choice_4,
            correct_choice_index=model.correct_choice_index,
            ehime_trivia=model.ehime_trivia,
            aws_ai_explanation=model.aws_ai_explanation,
            difficulty=Difficulty(model.difficulty),
            exam_domain=model.exam_domain,
        )
