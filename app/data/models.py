"""
愛媛探索AIクイズ - SQLAlchemy ORM モデル定義

ドメインエンティティに対応するデータベーステーブルを定義する。
SQLAlchemy 2.0 スタイル（mapped_column）を使用。
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.database import Base


class CourseModel(Base):
    """コーステーブル"""

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str] = mapped_column(String(20), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # リレーション
    questions: Mapped[list["QuestionModel"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    quiz_sessions: Mapped[list["QuizSessionModel"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class QuestionModel(Base):
    """問題テーブル"""

    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, unique=True)
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    choice_1: Mapped[str] = mapped_column(Text, nullable=False)
    choice_2: Mapped[str] = mapped_column(Text, nullable=False)
    choice_3: Mapped[str] = mapped_column(Text, nullable=False)
    choice_4: Mapped[str] = mapped_column(Text, nullable=False)
    correct_choice_index: Mapped[int] = mapped_column(Integer, nullable=False)
    ehime_trivia: Mapped[str] = mapped_column(Text, nullable=False)
    aws_ai_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    exam_domain: Mapped[str] = mapped_column(String(100), nullable=False)

    # リレーション
    course: Mapped["CourseModel"] = relationship(back_populates="questions")


class UserModel(Base):
    """ユーザーテーブル"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    total_xp: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    level: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    # リレーション
    answer_records: Mapped[list["AnswerRecordModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    quiz_sessions: Mapped[list["QuizSessionModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    mock_exam_sessions: Mapped[list["MockExamSessionModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AnswerRecordModel(Base):
    """回答記録テーブル"""

    __tablename__ = "answer_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        ForeignKey("questions.id"), nullable=False
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id"), nullable=False
    )
    selected_choice_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # リレーション
    user: Mapped["UserModel"] = relationship(back_populates="answer_records")


class QuizSessionModel(Base):
    """クイズセッションテーブル"""

    __tablename__ = "quiz_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress"
    )

    # リレーション
    user: Mapped["UserModel"] = relationship(back_populates="quiz_sessions")
    course: Mapped["CourseModel"] = relationship(back_populates="quiz_sessions")


class MockExamSessionModel(Base):
    """模擬試験セッションテーブル"""

    __tablename__ = "mock_exam_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    exam_type: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress"
    )

    # リレーション
    user: Mapped["UserModel"] = relationship(back_populates="mock_exam_sessions")


class MockExamResultModel(Base):
    """模擬試験結果テーブル"""

    __tablename__ = "mock_exam_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    exam_type: Mapped[str] = mapped_column(String(100), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    score_percentage: Mapped[float] = mapped_column(nullable=False)
    grade: Mapped[str] = mapped_column(String(5), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
