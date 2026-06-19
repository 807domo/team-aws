"""
採点モジュールのプロパティベーステスト

Property 4: 正答率計算
Property 5: グレード判定
Property 7: ドメイン別正答率計算
"""

from datetime import datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.domain.models import AnswerRecord, Grade
from app.domain.scoring import (
    calculate_accuracy_rate,
    calculate_domain_accuracy,
    calculate_grade,
)


# =============================================================================
# Property 4: Accuracy rate calculation
# =============================================================================


@settings(max_examples=100)
@given(
    correct_count=st.integers(min_value=0, max_value=1000),
    total_count=st.integers(min_value=1, max_value=1000),
)
def test_accuracy_rate_calculation(correct_count: int, total_count: int):
    """
    Feature: ehime-ai-quiz, Property 4: Accuracy rate calculation

    For any non-empty sequence of answer results, the calculated accuracy rate
    SHALL equal round(correct_count / total_count * 100, 1).

    Validates: Requirements 4.2, 4.3, 2.5
    """
    # Ensure correct_count <= total_count
    correct_count = min(correct_count, total_count)

    result = calculate_accuracy_rate(correct_count, total_count)
    expected = round(correct_count / total_count * 100, 1)

    assert result == expected


@settings(max_examples=100)
@given(
    correct_count=st.integers(min_value=0, max_value=1000),
    total_count=st.integers(min_value=1, max_value=1000),
)
def test_accuracy_rate_range(correct_count: int, total_count: int):
    """
    Feature: ehime-ai-quiz, Property 4: Accuracy rate calculation

    Accuracy rate SHALL always be in range [0.0, 100.0].

    Validates: Requirements 4.2, 4.3, 2.5
    """
    correct_count = min(correct_count, total_count)

    result = calculate_accuracy_rate(correct_count, total_count)

    assert 0.0 <= result <= 100.0


# =============================================================================
# Property 5: Grade assignment from score
# =============================================================================


@settings(max_examples=100)
@given(score=st.floats(min_value=0.0, max_value=100.0))
def test_grade_assignment_from_score(score: float):
    """
    Feature: ehime-ai-quiz, Property 5: Grade assignment from score

    For any score percentage in [0, 100], grade SHALL be:
    A if score >= 90, B if 80 <= score < 90, C if 70 <= score < 80,
    D if 60 <= score < 70, E if score < 60.

    Validates: Requirements 5.3, 6.1
    """
    grade = calculate_grade(score)

    if score >= 90:
        assert grade == Grade.A
    elif score >= 80:
        assert grade == Grade.B
    elif score >= 70:
        assert grade == Grade.C
    elif score >= 60:
        assert grade == Grade.D
    else:
        assert grade == Grade.E


@settings(max_examples=100)
@given(score=st.floats(min_value=0.0, max_value=100.0))
def test_grade_is_always_valid(score: float):
    """
    Feature: ehime-ai-quiz, Property 5: Grade assignment from score

    Grade assignment SHALL always return a valid Grade enum value.

    Validates: Requirements 5.3, 6.1
    """
    grade = calculate_grade(score)

    assert grade in (Grade.A, Grade.B, Grade.C, Grade.D, Grade.E)


# =============================================================================
# Property 7: Domain-level accuracy calculation
# =============================================================================

# Strategy for generating domain labels
DOMAIN_LABELS = [
    "Cloud Concepts",
    "Security",
    "Technology",
    "Billing",
    "Fundamentals",
    "Generative AI",
    "Responsible AI",
]

domain_strategy = st.sampled_from(DOMAIN_LABELS)


@st.composite
def answer_records_with_domains(draw):
    """Generate a list of AnswerRecords with associated domain mappings."""
    num_records = draw(st.integers(min_value=1, max_value=50))

    records = []
    question_domains = {}

    for i in range(num_records):
        question_id = f"q_{i}"
        domain = draw(domain_strategy)
        is_correct = draw(st.booleans())

        question_domains[question_id] = domain
        records.append(
            AnswerRecord(
                id=f"ar_{i}",
                user_id="user_1",
                question_id=question_id,
                course_id="course_1",
                selected_choice_index=0,
                is_correct=is_correct,
                answered_at=datetime.now(),
            )
        )

    return records, question_domains


@settings(max_examples=100)
@given(data=answer_records_with_domains())
def test_domain_level_accuracy_calculation(data):
    """
    Feature: ehime-ai-quiz, Property 7: Domain-level accuracy calculation

    For any set of answer records with domain labels, per-domain accuracy
    SHALL equal round(domain_correct / domain_total * 100, 1).

    Validates: Requirements 6.2
    """
    records, question_domains = data

    result = calculate_domain_accuracy(records, question_domains)

    # Manually compute expected values
    domain_correct: dict[str, int] = {}
    domain_total: dict[str, int] = {}

    for record in records:
        domain = question_domains.get(record.question_id)
        if domain is None:
            continue
        domain_total[domain] = domain_total.get(domain, 0) + 1
        if record.is_correct:
            domain_correct[domain] = domain_correct.get(domain, 0) + 1

    for domain, total in domain_total.items():
        correct = domain_correct.get(domain, 0)
        expected = round(correct / total * 100, 1)
        assert result[domain] == expected, (
            f"Domain '{domain}': expected {expected}, got {result[domain]}"
        )


@settings(max_examples=100)
@given(data=answer_records_with_domains())
def test_domain_accuracy_values_in_range(data):
    """
    Feature: ehime-ai-quiz, Property 7: Domain-level accuracy calculation

    All domain accuracy values SHALL be in range [0.0, 100.0].

    Validates: Requirements 6.2
    """
    records, question_domains = data

    result = calculate_domain_accuracy(records, question_domains)

    for domain, accuracy in result.items():
        assert 0.0 <= accuracy <= 100.0, (
            f"Domain '{domain}' accuracy {accuracy} out of range"
        )
