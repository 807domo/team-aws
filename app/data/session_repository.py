"""
愛媛探索AIクイズ - Session Repository

クイズセッションデータへのアクセスを提供するリポジトリクラス。
SQLAlchemy Session をコンストラクタインジェクションで受け取り、テスト容易性を確保する。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.data.models import QuizSessionModel
from app.domain.models import QuizSession, SessionStatus


class SessionRepository:
    """クイズセッションデータへのアクセスを提供するリポジトリ"""

    def __init__(self, session: Session) -> None:
        self._db = session

    def create(self, quiz_session: QuizSession) -> QuizSession:
        """新しいクイズセッションを作成する。

        Args:
            quiz_session: 作成するクイズセッションのドメインオブジェクト

        Returns:
            作成されたクイズセッションのドメインオブジェクト
        """
        db_session = QuizSessionModel(
            id=quiz_session.id,
            user_id=quiz_session.user_id,
            course_id=quiz_session.course_id,
            started_at=quiz_session.started_at,
            completed_at=quiz_session.completed_at,
            status=quiz_session.status.value,
        )
        self._db.add(db_session)
        self._db.commit()
        return quiz_session

    def get_by_id(self, session_id: str) -> Optional[QuizSession]:
        """セッションIDを指定してクイズセッションを取得する。

        Args:
            session_id: クイズセッションID

        Returns:
            該当するQuizSessionオブジェクト。存在しない場合はNone。
        """
        model = (
            self._db.query(QuizSessionModel)
            .filter(QuizSessionModel.id == session_id)
            .first()
        )
        if model is None:
            return None
        return self._to_domain(model)

    def get_by_user_and_status(
        self, user_id: str, status: SessionStatus
    ) -> list[QuizSession]:
        """ユーザーIDとステータスを指定してセッション一覧を取得する。

        Args:
            user_id: ユーザーID
            status: セッションステータス

        Returns:
            条件に合致するQuizSessionオブジェクトのリスト
        """
        models = (
            self._db.query(QuizSessionModel)
            .filter(
                QuizSessionModel.user_id == user_id,
                QuizSessionModel.status == status.value,
            )
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_user_course_status(
        self, user_id: str, course_id: str, statuses: list[SessionStatus]
    ) -> list[QuizSession]:
        """ユーザーID、コースID、ステータスリストを指定してセッション一覧を取得する。

        Args:
            user_id: ユーザーID
            course_id: コースID
            statuses: 検索対象のセッションステータスリスト

        Returns:
            条件に合致するQuizSessionオブジェクトのリスト
        """
        status_values = [s.value for s in statuses]
        models = (
            self._db.query(QuizSessionModel)
            .filter(
                QuizSessionModel.user_id == user_id,
                QuizSessionModel.course_id == course_id,
                QuizSessionModel.status.in_(status_values),
            )
            .order_by(QuizSessionModel.started_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def update_status(
        self,
        session_id: str,
        status: SessionStatus,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """セッションのステータスを更新する。

        Args:
            session_id: クイズセッションID
            status: 更新先のセッションステータス
            completed_at: 完了日時（COMPLETED時に設定）
        """
        model = (
            self._db.query(QuizSessionModel)
            .filter(QuizSessionModel.id == session_id)
            .first()
        )
        if model is not None:
            model.status = status.value
            if completed_at is not None:
                model.completed_at = completed_at
            self._db.commit()

    def get_in_progress_by_user_except_course(
        self, user_id: str, exclude_course_id: str
    ) -> list[QuizSession]:
        """指定コース以外のユーザーのIN_PROGRESSセッションを取得する。

        Args:
            user_id: ユーザーID
            exclude_course_id: 除外するコースID

        Returns:
            条件に合致するQuizSessionオブジェクトのリスト
        """
        models = (
            self._db.query(QuizSessionModel)
            .filter(
                QuizSessionModel.user_id == user_id,
                QuizSessionModel.course_id != exclude_course_id,
                QuizSessionModel.status == SessionStatus.IN_PROGRESS.value,
            )
            .all()
        )
        return [self._to_domain(m) for m in models]

    @staticmethod
    def _to_domain(model: QuizSessionModel) -> QuizSession:
        """SQLAlchemy ORMモデルをドメインモデルに変換する。"""
        return QuizSession(
            id=model.id,
            user_id=model.user_id,
            course_id=model.course_id,
            started_at=model.started_at,
            completed_at=model.completed_at,
            status=SessionStatus(model.status),
        )
