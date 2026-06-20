"""
愛媛探索AIクイズ - User Record Repository

回答記録の保存・取得とユーザーの正答率計算を行うリポジトリ。
SQLAlchemy Session をコンストラクタインジェクションで受け取る。
"""

from sqlalchemy.orm import Session

from app.data.models import AnswerRecordModel, UserModel
from app.domain.models import AnswerRecord
from app.domain.scoring import calculate_accuracy_rate


class UserRecordRepository:
    """ユーザー回答記録リポジトリ"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save_answer_record(self, record: AnswerRecord) -> AnswerRecord:
        """回答記録を保存する。

        同一問題への再回答も含めて全回答を記録する（Req 4.4）。

        Args:
            record: 保存する回答記録（ドメインモデル）

        Returns:
            保存された回答記録（ドメインモデル）
        """
        db_record = AnswerRecordModel(
            id=record.id,
            user_id=record.user_id,
            question_id=record.question_id,
            course_id=record.course_id,
            selected_choice_index=record.selected_choice_index,
            is_correct=record.is_correct,
            answered_at=record.answered_at,
        )
        self._session.add(db_record)
        self._session.commit()
        self._session.refresh(db_record)
        return self._to_domain(db_record)

    def get_records_by_user(self, user_id: str) -> list[AnswerRecord]:
        """ユーザーの全回答記録を取得する。

        Args:
            user_id: ユーザーID

        Returns:
            該当ユーザーの全回答記録リスト
        """
        db_records = (
            self._session.query(AnswerRecordModel)
            .filter(AnswerRecordModel.user_id == user_id)
            .all()
        )
        return [self._to_domain(r) for r in db_records]

    def get_records_by_user_and_course(
        self, user_id: str, course_id: str
    ) -> list[AnswerRecord]:
        """ユーザー＋コース別の回答記録を取得する。

        Args:
            user_id: ユーザーID
            course_id: コースID

        Returns:
            該当ユーザー・コースの回答記録リスト
        """
        db_records = (
            self._session.query(AnswerRecordModel)
            .filter(
                AnswerRecordModel.user_id == user_id,
                AnswerRecordModel.course_id == course_id,
            )
            .all()
        )
        return [self._to_domain(r) for r in db_records]

    def get_accuracy_by_course(self, user_id: str, course_id: str) -> float:
        """コース別正答率を返す。

        scoring.calculate_accuracy_rate を使用して計算する。
        回答がない場合は 0.0 を返す。

        Args:
            user_id: ユーザーID
            course_id: コースID

        Returns:
            正答率（0.0〜100.0、小数第1位まで）
        """
        records = self.get_records_by_user_and_course(user_id, course_id)
        total_count = len(records)
        correct_count = sum(1 for r in records if r.is_correct)
        return calculate_accuracy_rate(correct_count, total_count)

    def get_cumulative_accuracy(self, user_id: str) -> float:
        """全体正答率を返す。

        全コースの回答を合算して正答率を計算する。
        回答がない場合は 0.0 を返す。

        Args:
            user_id: ユーザーID

        Returns:
            全体正答率（0.0〜100.0、小数第1位まで）
        """
        records = self.get_records_by_user(user_id)
        total_count = len(records)
        correct_count = sum(1 for r in records if r.is_correct)
        return calculate_accuracy_rate(correct_count, total_count)

    def get_user_xp(self, user_id: str) -> dict:
        """ユーザーのXPとレベルを取得する。

        DB null や不正データ（負値など）の場合はフォールバック値を返す。

        Args:
            user_id: ユーザーID

        Returns:
            {"total_xp": int, "level": int}
            - total_xp: 累計XP（フォールバック: 0）
            - level: 現在レベル（フォールバック: 1）
        """
        user = (
            self._session.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )
        if user is None:
            return {"total_xp": 0, "level": 1}

        total_xp = user.total_xp
        level = user.level

        # null または不正データ時のフォールバック
        if total_xp is None or not isinstance(total_xp, int) or total_xp < 0:
            total_xp = 0
        if level is None or not isinstance(level, int) or level < 1:
            level = 1

        return {"total_xp": total_xp, "level": level}

    def update_user_xp_and_level(
        self, user_id: str, total_xp: int, level: int
    ) -> None:
        """ユーザーのXPとレベルを永続化する。

        Args:
            user_id: ユーザーID
            total_xp: 新しい累計XP（0以上）
            level: 新しいレベル（1以上）

        Raises:
            ValueError: total_xp が負、または level が1未満の場合
        """
        if total_xp < 0:
            raise ValueError(f"total_xp must be non-negative, got {total_xp}")
        if level < 1:
            raise ValueError(f"level must be at least 1, got {level}")

        user = (
            self._session.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )
        if user is None:
            return

        user.total_xp = total_xp
        user.level = level
        self._session.commit()

    @staticmethod
    def _to_domain(db_record: AnswerRecordModel) -> AnswerRecord:
        """SQLAlchemy モデルからドメインモデルに変換する。"""
        return AnswerRecord(
            id=db_record.id,
            user_id=db_record.user_id,
            question_id=db_record.question_id,
            course_id=db_record.course_id,
            selected_choice_index=db_record.selected_choice_index,
            is_correct=db_record.is_correct,
            answered_at=db_record.answered_at,
        )
