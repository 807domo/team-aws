"""
弱点特定のプロパティベーステスト

Property 8: Weak area identification
"""

from datetime import datetime

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.domain.models import AnswerRecord, WeakArea
from app.domain.scoring import identify_weak_areas


# =============================================================================
# Property 8: Weak area identification
# =============================================================================

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
def answer_records_with_many_incorrect(draw):
    """
    Generate answer records with at least 10 incorrect answers total.
    Each record has an associated domain via question_domains mapping.
    """
    # Generate between 10 and 80 records to ensure enough data
    num_records = draw(st.integers(min_value=20, max_value=80))

    records = []
    question_domains = {}
    incorrect_count = 0

    for i in range(num_records):
        question_id = f"q_{i}"
        domain = draw(domain_strategy)
        is_correct = draw(st.booleans())

        if not is_correct:
            incorrect_count += 1

        question_domains[question_id] = domain
        records.append(
            AnswerRecord(
                id=f"ar_{i}",
                user_id="user_1",
                question_id=question_id,
                course_id="course_1",
                selected_choice_index=0 if is_correct else 1,
                is_correct=is_correct,
                answered_at=datetime.now(),
            )
        )

    # Ensure at least 10 incorrect answers
    assume(incorrect_count >= 10)

    return records, question_domains


@settings(max_examples=100)
@given(data=answer_records_with_many_incorrect())
def test_weak_area_identification(data):
    """
    Feature: ehime-ai-quiz, Property 8: Weak area identification

    For any set of answer records where the user has 10+ incorrect answers,
    a domain SHALL be identified as a weak area if and only if its
    incorrect rate is 50% or higher (incorrect_count / total_count >= 0.5).

    Validates: Requirements 8.1
    """
    records, question_domains = data

    result = identify_weak_areas(records, question_domains, threshold=0.5)

    # Manually compute domain-level incorrect rates
    domain_correct: dict[str, int] = {}
    domain_total: dict[str, int] = {}

    for record in records:
        domain = question_domains.get(record.question_id)
        if domain is None:
            continue
        domain_total[domain] = domain_total.get(domain, 0) + 1
        if record.is_correct:
            domain_correct[domain] = domain_correct.get(domain, 0) + 1

    # Check that each domain with incorrect_rate >= 50% is a weak area
    weak_domains_in_result = {wa.domain for wa in result}

    for domain, total in domain_total.items():
        correct = domain_correct.get(domain, 0)
        incorrect = total - correct
        incorrect_rate = incorrect / total

        if incorrect_rate >= 0.5:
            assert domain in weak_domains_in_result, (
                f"Domain '{domain}' with incorrect_rate={incorrect_rate:.2f} "
                f"should be a weak area but was not identified"
            )
        else:
            assert domain not in weak_domains_in_result, (
                f"Domain '{domain}' with incorrect_rate={incorrect_rate:.2f} "
                f"should NOT be a weak area but was identified"
            )


@settings(max_examples=100)
@given(data=answer_records_with_many_incorrect())
def test_weak_area_incorrect_rate_values(data):
    """
    Feature: ehime-ai-quiz, Property 8: Weak area identification

    Each weak area's incorrect_rate SHALL equal
    round(incorrect_count / total_count * 100, 1) for that domain.

    Validates: Requirements 8.1
    """
    records, question_domains = data

    result = identify_weak_areas(records, question_domains, threshold=0.5)

    # Manually compute expected incorrect rates
    domain_correct: dict[str, int] = {}
    domain_total: dict[str, int] = {}

    for record in records:
        domain = question_domains.get(record.question_id)
        if domain is None:
            continue
        domain_total[domain] = domain_total.get(domain, 0) + 1
        if record.is_correct:
            domain_correct[domain] = domain_correct.get(domain, 0) + 1

    for weak_area in result:
        total = domain_total[weak_area.domain]
        correct = domain_correct.get(weak_area.domain, 0)
        incorrect = total - correct
        expected_rate = round(incorrect / total * 100, 1)

        assert weak_area.incorrect_rate == expected_rate, (
            f"Domain '{weak_area.domain}': expected incorrect_rate={expected_rate}, "
            f"got {weak_area.incorrect_rate}"
        )
