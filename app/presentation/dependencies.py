"""
愛媛探索AIクイズ - Dependency Injection（DI）定義

FastAPI の Depends() で使用する依存性注入関数を定義する。
リポジトリおよびサービスのインスタンスを注入し、
プレゼンテーション層からドメイン層・データ層への依存を管理する。
"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.repository_factory import (
    get_course_repository as _get_course_repo,
    get_question_repository as _get_question_repo,
    get_user_record_repository as _get_user_record_repo,
)
from app.domain.auth_service import AuthService
from app.domain.mock_exam_engine import MockExamEngine
from app.domain.quiz_service import QuizService
from app.domain.results_service import ResultsService

# Cookieからセッションを読み取るためのCookie名
SESSION_COOKIE_NAME = "session_token"


# =============================================================================
# 認証関連の依存性注入
# =============================================================================


def get_current_user_id(request: Request) -> str:
    """現在ログイン中のユーザーIDを取得する。

    Cookieのセッショントークンからユーザーを特定する。
    未ログインの場合はログイン画面にリダイレクトする。

    Raises:
        RequiresLoginException: 未ログイン時にログイン画面へリダイレクト
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    user_id = AuthService.get_user_id_from_session(token)
    if user_id is None:
        raise RequiresLoginException()
    return user_id


class RequiresLoginException(Exception):
    """未ログイン時に発生する例外。ログイン画面へのリダイレクトをトリガーする。"""
    pass


# =============================================================================
# リポジトリの依存性注入
# =============================================================================


def get_course_repository(db: Session = Depends(get_db)):
    """CourseRepository インスタンスを生成する。"""
    return _get_course_repo(db)


def get_question_repository(db: Session = Depends(get_db)):
    """QuestionRepository インスタンスを生成する。"""
    return _get_question_repo(db)


def get_user_record_repository(db: Session = Depends(get_db)):
    """UserRecordRepository インスタンスを生成する。"""
    return _get_user_record_repo(db)


# =============================================================================
# サービスの依存性注入
# =============================================================================


def get_quiz_service(db: Session = Depends(get_db)) -> QuizService:
    """QuizService インスタンスを生成する。"""
    return QuizService(db)


def get_results_service(
    db: Session = Depends(get_db),
) -> ResultsService:
    """ResultsService インスタンスを生成する。"""
    return ResultsService(
        user_record_repository=_get_user_record_repo(db),
        course_repository=_get_course_repo(db),
        question_repository=_get_question_repo(db),
    )


# MockExamEngine シングルトンインスタンス（インメモリセッション管理のため）
_mock_exam_engine_instance: MockExamEngine | None = None


def get_mock_exam_engine(
    db: Session = Depends(get_db),
) -> MockExamEngine:
    """MockExamEngine シングルトンインスタンスを返す。"""
    global _mock_exam_engine_instance
    if _mock_exam_engine_instance is None:
        _mock_exam_engine_instance = MockExamEngine(question_repository=_get_question_repo(db))
    return _mock_exam_engine_instance
