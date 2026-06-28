"""
愛媛探索AIクイズ - Dependency Injection（DI）定義

FastAPI の Depends() で使用する依存性注入関数を定義する。
リポジトリおよびサービスのインスタンスを注入し、
プレゼンテーション層からドメイン層・データ層への依存を管理する。
"""

from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.data.course_repository import CourseRepository
from app.data.database import get_db
from app.data.question_repository import QuestionRepository
from app.data.user_record_repository import UserRecordRepository
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
        RedirectResponse: 未ログイン時にログイン画面へリダイレクト
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


def get_course_repository(db: Session = Depends(get_db)) -> CourseRepository:
    """CourseRepository インスタンスを生成する。"""
    return CourseRepository(db)


def get_question_repository(db: Session = Depends(get_db)) -> QuestionRepository:
    """QuestionRepository インスタンスを生成する。"""
    return QuestionRepository(db)


def get_user_record_repository(db: Session = Depends(get_db)) -> UserRecordRepository:
    """UserRecordRepository インスタンスを生成する。"""
    return UserRecordRepository(db)


# =============================================================================
# サービスの依存性注入
# =============================================================================


def get_quiz_service(db: Session = Depends(get_db)) -> QuizService:
    """QuizService インスタンスを生成する。

    QuizService は内部でリポジトリを作成するため、
    DB セッションのみを注入する。
    """
    return QuizService(db)


def get_results_service(
    user_record_repo: UserRecordRepository = Depends(get_user_record_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
) -> ResultsService:
    """ResultsService インスタンスを生成する。

    ResultsService は複数のリポジトリを受け取るため、
    個別にリポジトリを注入する。
    """
    return ResultsService(
        user_record_repository=user_record_repo,
        course_repository=course_repo,
        question_repository=question_repo,
    )


# MockExamEngine シングルトンインスタンス（インメモリセッション管理のため）
_mock_exam_engine_instance: MockExamEngine | None = None


def get_mock_exam_engine(
    question_repo: QuestionRepository = Depends(get_question_repository),
) -> MockExamEngine:
    """MockExamEngine シングルトンインスタンスを返す。

    模擬試験はインメモリでセッションを管理するため、
    リクエスト間でインスタンスを共有する必要がある。
    """
    global _mock_exam_engine_instance
    if _mock_exam_engine_instance is None:
        _mock_exam_engine_instance = MockExamEngine(question_repository=question_repo)
    return _mock_exam_engine_instance
