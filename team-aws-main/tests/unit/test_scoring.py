"""
採点モジュールのユニットテスト
"""

from datetime import datetime

from app.domain.models import AnswerRecord, Grade, WeakArea
from app.domain.scoring import (
    calculate_accuracy_rate,
    calculate_domain_accuracy,
    calculate_grade,
    identify_weak_areas,
)


class TestCalculateAccuracyRate:
    """calculate_accuracy_rate のユニットテスト"""

    def test_zero_total_returns_zero(self):
        assert calculate_accuracy_rate(0, 0) == 0.0

    def test_all_correct(self):
        assert calculate_accuracy_rate(10, 10) == 100.0

    def test_all_incorrect(self):
        assert calculate_accuracy_rate(0, 10) == 0.0

    def test_partial_correct(self):
        assert calculate_accuracy_rate(7, 10) == 70.0

    def test_rounds_to_one_decimal(self):
        # 1/3 = 33.333...% -> 33.3
        assert calculate_accuracy_rate(1, 3) == 33.3

    def test_two_thirds(self):
        # 2/3 = 66.666...% -> 66.7
        assert calculate_accuracy_rate(2, 3) == 66.7


class TestCalculateGrade:
    """calculate_grade のユニットテスト"""

    def test_grade_a_at_90(self):
        assert calculate_grade(90.0) == Grade.A

    def test_grade_a_at_100(self):
        assert calculate_grade(100.0) == Grade.A

    def test_grade_b_at_80(self):
        assert calculate_grade(80.0) == Grade.B

    def test_grade_b_at_89(self):
        assert calculate_grade(89.9) == Grade.B

    def test_grade_c_at_70(self):
        assert calculate_grade(70.0) == Grade.C

    def test_grade_c_at_79(self):
        assert calculate_grade(79.9) == Grade.C

    def test_grade_d_at_60(self):
        assert calculate_grade(60.0) == Grade.D

    def test_grade_d_at_69(self):
        assert calculate_grade(69.9) == Grade.D

    def test_grade_e_at_59(self):
        assert calculate_grade(59.9) == Grade.E

    def test_grade_e_at_0(self):
        assert calculate_grade(0.0) == Grade.E


class TestCalculateDomainAccuracy:
    """calculate_domain_accuracy のユニットテスト"""

    def _make_record(self, question_id: str, is_correct: bool) -> AnswerRecord:
        return AnswerRecord(
            id="rec-1",
            user_id="user-1",
            question_id=question_id,
            course_id="course-1",
            selected_choice_index=0,
            is_correct=is_correct,
            answered_at=datetime.now(),
        )

    def test_empty_records(self):
        result = calculate_domain_accuracy([], {})
        assert result == {}

    def test_single_domain_all_correct(self):
        records = [
            self._make_record("q1", True),
            self._make_record("q2", True),
        ]
        domains = {"q1": "Cloud Concepts", "q2": "Cloud Concepts"}
        result = calculate_domain_accuracy(records, domains)
        assert result == {"Cloud Concepts": 100.0}

    def test_multiple_domains(self):
        records = [
            self._make_record("q1", True),
            self._make_record("q2", False),
            self._make_record("q3", True),
            self._make_record("q4", True),
        ]
        domains = {
            "q1": "Security",
            "q2": "Security",
            "q3": "Technology",
            "q4": "Technology",
        }
        result = calculate_domain_accuracy(records, domains)
        assert result == {"Security": 50.0, "Technology": 100.0}

    def test_question_without_domain_ignored(self):
        records = [self._make_record("q1", True)]
        domains = {}  # q1 has no domain mapping
        result = calculate_domain_accuracy(records, domains)
        assert result == {}


class TestIdentifyWeakAreas:
    """identify_weak_areas のユニットテスト"""

    def _make_record(self, question_id: str, is_correct: bool) -> AnswerRecord:
        return AnswerRecord(
            id="rec-1",
            user_id="user-1",
            question_id=question_id,
            course_id="course-1",
            selected_choice_index=0,
            is_correct=is_correct,
            answered_at=datetime.now(),
        )

    def test_empty_records(self):
        result = identify_weak_areas([], {})
        assert result == []

    def test_no_weak_areas_when_all_correct(self):
        records = [
            self._make_record("q1", True),
            self._make_record("q2", True),
        ]
        domains = {"q1": "Security", "q2": "Security"}
        result = identify_weak_areas(records, domains)
        assert result == []

    def test_identifies_weak_domain(self):
        records = [
            self._make_record("q1", False),
            self._make_record("q2", False),
            self._make_record("q3", True),
        ]
        domains = {"q1": "Security", "q2": "Security", "q3": "Technology"}
        result = identify_weak_areas(records, domains)
        assert len(result) == 1
        assert result[0].domain == "Security"
        assert result[0].incorrect_rate == 100.0

    def test_threshold_boundary_exactly_50_percent(self):
        records = [
            self._make_record("q1", True),
            self._make_record("q2", False),
        ]
        domains = {"q1": "Security", "q2": "Security"}
        result = identify_weak_areas(records, domains)
        # 50% incorrect rate == threshold (0.5), so it IS a weak area
        assert len(result) == 1
        assert result[0].domain == "Security"
        assert result[0].incorrect_rate == 50.0

    def test_below_threshold_not_weak(self):
        records = [
            self._make_record("q1", True),
            self._make_record("q2", True),
            self._make_record("q3", False),
        ]
        domains = {"q1": "Security", "q2": "Security", "q3": "Security"}
        # 1/3 incorrect = 33.3% < 50% threshold
        result = identify_weak_areas(records, domains)
        assert result == []

    def test_custom_threshold(self):
        records = [
            self._make_record("q1", True),
            self._make_record("q2", True),
            self._make_record("q3", False),
        ]
        domains = {"q1": "Security", "q2": "Security", "q3": "Security"}
        # 1/3 incorrect = 33.3% >= 30% threshold
        result = identify_weak_areas(records, domains, threshold=0.3)
        assert len(result) == 1
        assert result[0].domain == "Security"
