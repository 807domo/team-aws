"""
UserRecordRepository のユニットテスト

SQLite インメモリDBを使用して回答記録の保存・取得・正答率計算をテストする。
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.data.database import Base
from app.data.models import (
    AnswerRecordModel,
    CourseModel,
    QuestionModel,
    UserModel,
)
from app.data.user_record_repository import UserRecordRepository
from app.domain.models import AnswerRecord


@pytest.fixture
def session():
    """テスト用のインメモリSQLiteセッションを作成する。"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()

    # テスト用の基本データを投入
    user = UserModel(id="user-1", display_name="テストユーザー")
    course = CourseModel(
        id="course-1",
        name="松山城コース",
        region="中予",
        difficulty="基礎",
        description="テストコース",
    )
    course2 = CourseModel(
        id="course-2",
        name="道後温泉コース",
        region="中予",
        difficulty="中級",
        description="テストコース2",
    )
    question1 = QuestionModel(
        id="q-1",
        course_id="course-1",
        text="テスト問題1",
        choice_1="A",
        choice_2="B",
        choice_3="C",
        choice_4="D",
        correct_choice_index=0,
        ehime_trivia="トリビア",
        aws_ai_explanation="解説",
        difficulty="基礎",
        exam_domain="Cloud Concepts",
    )
    question2 = QuestionModel(
        id="q-2",
        course_id="course-2",
        text="テスト問題2",
        choice_1="A",
        choice_2="B",
        choice_3="C",
        choice_4="D",
        correct_choice_index=1,
        ehime_trivia="トリビア2",
        aws_ai_explanation="解説2",
        difficulty="中級",
        exam_domain="Security",
    )
    db.add_all([user, course, course2, question1, question2])
    db.commit()

    yield db
    db.close()


@pytest.fixture
def repo(session: Session) -> UserRecordRepository:
    """UserRecordRepositoryインスタンスを作成する。"""
    return UserRecordRepository(session)


class TestSaveAnswerRecord:
    """save_answer_record のテスト"""

    def test_saves_and_returns_record(self, repo: UserRecordRepository):
        record = AnswerRecord(
            id="rec-1",
            user_id="user-1",
            question_id="q-1",
            course_id="course-1",
            selected_choice_index=0,
            is_correct=True,
            answered_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        result = repo.save_answer_record(record)

        assert result.id == "rec-1"
        assert result.user_id == "user-1"
        assert result.question_id == "q-1"
        assert result.course_id == "course-1"
        assert result.selected_choice_index == 0
        assert result.is_correct is True

    def test_saves_duplicate_question_answers(self, repo: UserRecordRepository):
        """同一問題への再回答も記録される（Req 4.4）"""
        record1 = AnswerRecord(
            id="rec-1",
            user_id="user-1",
            question_id="q-1",
            course_id="course-1",
            selected_choice_index=1,
            is_correct=False,
            answered_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        record2 = AnswerRecord(
            id="rec-2",
            user_id="user-1",
            question_id="q-1",
            course_id="course-1",
            selected_choice_index=0,
            is_correct=True,
            answered_at=datetime(2025, 1, 1, 12, 5, 0),
        )
        repo.save_answer_record(record1)
        repo.save_answer_record(record2)

        records = repo.get_records_by_user("user-1")
        assert len(records) == 2


class TestGetRecordsByUser:
    """get_records_by_user のテスト"""

    def test_returns_all_user_records(self, repo: UserRecordRepository):
        repo.save_answer_record(
            AnswerRecord(
                id="rec-1",
                user_id="user-1",
                question_id="q-1",
                course_id="course-1",
                selected_choice_index=0,
                is_correct=True,
                answered_at=datetime(2025, 1, 1, 12, 0, 0),
            )
        )
        repo.save_answer_record(
            AnswerRecord(
                id="rec-2",
                user_id="user-1",
                question_id="q-2",
                course_id="course-2",
                selected_choice_index=1,
                is_correct=True,
                answered_at=datetime(2025, 1, 1, 12, 1, 0),
            )
        )

        records = repo.get_records_by_user("user-1")
        assert len(records) == 2

    def test_returns_empty_for_unknown_user(self, repo: UserRecordRepository):
        records = repo.get_records_by_user("unknown-user")
        assert records == []


class TestGetRecordsByUserAndCourse:
    """get_records_by_user_and_course のテスト"""

    def test_filters_by_course(self, repo: UserRecordRepository):
        repo.save_answer_record(
            AnswerRecord(
                id="rec-1",
                user_id="user-1",
                question_id="q-1",
                course_id="course-1",
                selected_choice_index=0,
                is_correct=True,
                answered_at=datetime(2025, 1, 1, 12, 0, 0),
            )
        )
        repo.save_answer_record(
            AnswerRecord(
                id="rec-2",
                user_id="user-1",
                question_id="q-2",
                course_id="course-2",
                selected_choice_index=1,
                is_correct=False,
                answered_at=datetime(2025, 1, 1, 12, 1, 0),
            )
        )

        records = repo.get_records_by_user_and_course("user-1", "course-1")
        assert len(records) == 1
        assert records[0].course_id == "course-1"

    def test_returns_empty_for_no_records(self, repo: UserRecordRepository):
        records = repo.get_records_by_user_and_course("user-1", "course-99")
        assert records == []


class TestGetAccuracyByCourse:
    """get_accuracy_by_course のテスト"""

    def test_calculates_accuracy(self, repo: UserRecordRepository):
        repo.save_answer_record(
            AnswerRecord(
                id="rec-1",
                user_id="user-1",
                question_id="q-1",
                course_id="course-1",
                selected_choice_index=0,
                is_correct=True,
                answered_at=datetime(2025, 1, 1, 12, 0, 0),
            )
        )
        repo.save_answer_record(
            AnswerRecord(
                id="rec-2",
                user_id="user-1",
                question_id="q-1",
                course_id="course-1",
                selected_choice_index=1,
                is_correct=False,
                answered_at=datetime(2025, 1, 1, 12, 1, 0),
            )
        )

        accuracy = repo.get_accuracy_by_course("user-1", "course-1")
        assert accuracy == 50.0

    def test_returns_zero_for_no_records(self, repo: UserRecordRepository):
        accuracy = repo.get_accuracy_by_course("user-1", "course-99")
        assert accuracy == 0.0

    def test_includes_repeated_answers(self, repo: UserRecordRepository):
        """再回答を含めた正答率計算（Req 4.4）"""
        # 同じ問題に3回回答: 1回正解、2回不正解 → 33.3%
        for i, is_correct in enumerate([True, False, False]):
            repo.save_answer_record(
                AnswerRecord(
                    id=f"rec-{i}",
                    user_id="user-1",
                    question_id="q-1",
                    course_id="course-1",
                    selected_choice_index=0 if is_correct else 1,
                    is_correct=is_correct,
                    answered_at=datetime(2025, 1, 1, 12, i, 0),
                )
            )

        accuracy = repo.get_accuracy_by_course("user-1", "course-1")
        assert accuracy == 33.3


class TestGetCumulativeAccuracy:
    """get_cumulative_accuracy のテスト"""

    def test_calculates_across_all_courses(self, repo: UserRecordRepository):
        repo.save_answer_record(
            AnswerRecord(
                id="rec-1",
                user_id="user-1",
                question_id="q-1",
                course_id="course-1",
                selected_choice_index=0,
                is_correct=True,
                answered_at=datetime(2025, 1, 1, 12, 0, 0),
            )
        )
        repo.save_answer_record(
            AnswerRecord(
                id="rec-2",
                user_id="user-1",
                question_id="q-2",
                course_id="course-2",
                selected_choice_index=0,
                is_correct=False,
                answered_at=datetime(2025, 1, 1, 12, 1, 0),
            )
        )

        accuracy = repo.get_cumulative_accuracy("user-1")
        assert accuracy == 50.0

    def test_returns_zero_for_no_records(self, repo: UserRecordRepository):
        accuracy = repo.get_cumulative_accuracy("user-1")
        assert accuracy == 0.0

    def test_perfect_score(self, repo: UserRecordRepository):
        for i in range(5):
            repo.save_answer_record(
                AnswerRecord(
                    id=f"rec-{i}",
                    user_id="user-1",
                    question_id=f"q-{(i % 2) + 1}",
                    course_id=f"course-{(i % 2) + 1}",
                    selected_choice_index=0,
                    is_correct=True,
                    answered_at=datetime(2025, 1, 1, 12, i, 0),
                )
            )

        accuracy = repo.get_cumulative_accuracy("user-1")
        assert accuracy == 100.0
