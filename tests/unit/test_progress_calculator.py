"""
進捗ステータス算出モジュールのユニットテスト

Requirements: 7.2, 7.4
"""

from datetime import datetime

import pytest

from app.domain.models import AnswerRecord
from app.domain.progress_calculator import ProgressStatus, calculate_region_progress


def _make_answer_record(
    question_id: str,
    course_id: str,
    is_correct: bool,
    user_id: str = "user-1",
) -> AnswerRecord:
    """テスト用 AnswerRecord ヘルパー"""
    return AnswerRecord(
        id=f"ar-{question_id}-{course_id}",
        user_id=user_id,
        question_id=question_id,
        course_id=course_id,
        selected_choice_index=0 if is_correct else 1,
        is_correct=is_correct,
        answered_at=datetime(2025, 1, 1),
    )


class TestCalculateRegionProgress:
    """calculate_region_progress のユニットテスト"""

    def test_zero_courses_region_returns_complete(self):
        """ゼロコース地域 → COMPLETE"""
        result = calculate_region_progress(
            region="CHUYO",
            courses_in_region=[],
            user_answer_records=[],
            course_questions={},
        )
        assert result == ProgressStatus.COMPLETE

    def test_no_records_returns_not_started(self):
        """コースが存在するが回答記録なし → NOT_STARTED"""
        result = calculate_region_progress(
            region="NANYO",
            courses_in_region=["course-1", "course-2"],
            user_answer_records=[],
            course_questions={
                "course-1": ["q1", "q2"],
                "course-2": ["q3", "q4"],
            },
        )
        assert result == ProgressStatus.NOT_STARTED

    def test_partial_completion_returns_in_progress(self):
        """一部コースのみ完了 → IN_PROGRESS"""
        records = [
            # course-1 は全問正解
            _make_answer_record("q1", "course-1", is_correct=True),
            _make_answer_record("q2", "course-1", is_correct=True),
            # course-2 は q3 のみ正解、q4 未正解
            _make_answer_record("q3", "course-2", is_correct=True),
        ]
        result = calculate_region_progress(
            region="TOYO",
            courses_in_region=["course-1", "course-2"],
            user_answer_records=records,
            course_questions={
                "course-1": ["q1", "q2"],
                "course-2": ["q3", "q4"],
            },
        )
        assert result == ProgressStatus.IN_PROGRESS

    def test_all_courses_complete_returns_complete(self):
        """全コースで全問正解 → COMPLETE"""
        records = [
            _make_answer_record("q1", "course-1", is_correct=True),
            _make_answer_record("q2", "course-1", is_correct=True),
            _make_answer_record("q3", "course-2", is_correct=True),
            _make_answer_record("q4", "course-2", is_correct=True),
        ]
        result = calculate_region_progress(
            region="CHUYO",
            courses_in_region=["course-1", "course-2"],
            user_answer_records=records,
            course_questions={
                "course-1": ["q1", "q2"],
                "course-2": ["q3", "q4"],
            },
        )
        assert result == ProgressStatus.COMPLETE

    def test_some_wrong_answers_still_in_progress(self):
        """一部不正解がある場合 → IN_PROGRESS"""
        records = [
            # course-1: q1 正解、q2 不正解のみ
            _make_answer_record("q1", "course-1", is_correct=True),
            _make_answer_record("q2", "course-1", is_correct=False),
        ]
        result = calculate_region_progress(
            region="NANYO",
            courses_in_region=["course-1"],
            user_answer_records=records,
            course_questions={
                "course-1": ["q1", "q2"],
            },
        )
        assert result == ProgressStatus.IN_PROGRESS
