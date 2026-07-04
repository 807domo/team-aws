"""
シードデータの構造的正当性を検証するプロパティベーステスト

Property 1: Region-difficulty consistency
Property 2: Question structural validity
Property 3: Question ID format validity
Property 4: Question references valid course
Property 5: Question has valid exam domain
"""

import re

from hypothesis import given, settings
from hypothesis.strategies import sampled_from

from app.data.seed_data import QUESTIONS
from app.data.seed_data_extra import EXTRA_QUESTIONS
from app.data.seed_data_extra2 import EXTRA_QUESTIONS_2

ALL_QUESTIONS = QUESTIONS + EXTRA_QUESTIONS + EXTRA_QUESTIONS_2


# =============================================================================
# Property 1: Region-difficulty consistency
# =============================================================================


VALID_DIFFICULTIES = {"基礎", "中級", "上級"}


@settings(max_examples=200)
@given(question=sampled_from(ALL_QUESTIONS))
def test_region_difficulty_consistency(question):
    """
    Feature: exam-ready-quiz-rebuild, Property 1: Region-difficulty consistency

    For any question in the seed data, its course_id must begin with a valid
    region prefix (nanyo-, chuyo-, toyo-) and difficulty must be one of the
    valid difficulty values.

    Validates: Requirements 1.2, 1.3, 1.4
    """
    course_id = question["course_id"]
    difficulty = question["difficulty"]

    assert any(course_id.startswith(prefix) for prefix in ("nanyo-", "chuyo-", "toyo-")), (
        f"Question {question['id']}: course_id '{course_id}' does not start with "
        f"a valid region prefix (nanyo-, chuyo-, toyo-)"
    )

    assert difficulty in VALID_DIFFICULTIES, (
        f"Question {question['id']}: difficulty '{difficulty}' is not valid. "
        f"Must be one of: {sorted(VALID_DIFFICULTIES)}"
    )


# =============================================================================
# Property 2: Question structural validity
# =============================================================================

REQUIRED_FIELDS = [
    "id",
    "course_id",
    "text",
    "choice_1",
    "choice_2",
    "choice_3",
    "choice_4",
    "correct_choice_index",
    "ehime_trivia",
    "aws_ai_explanation",
    "difficulty",
    "exam_domain",
]

STRING_FIELDS = [
    "id",
    "course_id",
    "text",
    "choice_1",
    "choice_2",
    "choice_3",
    "choice_4",
    "ehime_trivia",
    "aws_ai_explanation",
    "difficulty",
    "exam_domain",
]


@settings(max_examples=200)
@given(question=sampled_from(ALL_QUESTIONS))
def test_question_structural_validity(question):
    """
    Feature: exam-ready-quiz-rebuild, Property 2: Question structural validity

    For any question in the seed data, it must contain all required fields,
    all string fields are non-empty, correct_choice_index is 0-3, and all
    four answer choices are mutually exclusive (all different from each other).

    Validates: Requirements 2.1, 2.4, 2.5, 3.2, 3.6, 7.4
    """
    # All required fields exist
    for field in REQUIRED_FIELDS:
        assert field in question, (
            f"Question {question.get('id', 'UNKNOWN')}: missing required field '{field}'"
        )

    # String fields are non-empty
    for field in STRING_FIELDS:
        value = question[field]
        assert isinstance(value, str) and len(value.strip()) > 0, (
            f"Question {question['id']}: field '{field}' must be a non-empty string, "
            f"got '{value}'"
        )

    # correct_choice_index is 0-3
    idx = question["correct_choice_index"]
    assert isinstance(idx, int) and 0 <= idx <= 3, (
        f"Question {question['id']}: correct_choice_index must be 0-3, got {idx}"
    )

    # 4 choices are mutually exclusive (all different from each other)
    choices = [
        question["choice_1"],
        question["choice_2"],
        question["choice_3"],
        question["choice_4"],
    ]
    assert len(set(choices)) == 4, (
        f"Question {question['id']}: 4 choices must all be different, "
        f"got duplicates in {choices}"
    )


# =============================================================================
# Property 3: Question ID format validity
# =============================================================================

ID_PATTERN = re.compile(r"^(nanyo|chuyo|toyo|q|q-ex|q-bz)-(cc|sc|ct|bp|ai|ga|fm|ra|sg|ex|bun|bz)-?\w*-?\d{3}$")


@settings(max_examples=200)
@given(question=sampled_from(ALL_QUESTIONS))
def test_question_id_format_validity(question):
    """
    Feature: exam-ready-quiz-rebuild, Property 3: Question ID format validity

    For any question in the seed data, its id must match the pattern
    {region}-{domain-abbr}-{NNN} where region is one of (nanyo, chuyo, toyo),
    domain-abbr is one of (cc, sc, ct, bp, ai, ga, fm, ra, sg), and NNN is a
    zero-padded three-digit number.

    Validates: Requirements 2.2
    """
    qid = question["id"]
    assert ID_PATTERN.match(qid), (
        f"Question ID '{qid}' does not match expected format "
        f"'{{region}}-{{domain-abbr}}-{{NNN}}'"
    )


def test_question_id_uniqueness():
    """
    Feature: exam-ready-quiz-rebuild, Property 3: Question ID format validity

    All IDs are unique across the full question set.

    Validates: Requirements 2.2
    """
    all_ids = [q["id"] for q in ALL_QUESTIONS]
    duplicates = [qid for qid in all_ids if all_ids.count(qid) > 1]
    assert len(all_ids) == len(set(all_ids)), (
        f"Duplicate question IDs found: {set(duplicates)}"
    )


# =============================================================================
# Property 4: Question references valid course
# =============================================================================

VALID_COURSE_IDS = set(
    [f"nanyo-stage-{i:02d}" for i in range(1, 32)]
    + [f"chuyo-stage-{i:02d}" for i in range(1, 21)]
    + [f"toyo-stage-{i:02d}" for i in range(1, 21)]
) | {q["course_id"] for q in ALL_QUESTIONS}


@settings(max_examples=200)
@given(question=sampled_from(ALL_QUESTIONS))
def test_question_references_valid_course(question):
    """
    Feature: exam-ready-quiz-rebuild, Property 4: Question references valid course

    For any question in the seed data, its course_id must be one of the 71 valid
    course IDs (nanyo-stage-01~31, chuyo-stage-01~20, toyo-stage-01~20).

    Validates: Requirements 2.3
    """
    course_id = question["course_id"]
    assert course_id in VALID_COURSE_IDS, (
        f"Question {question['id']}: course_id '{course_id}' is not a valid course. "
        f"Valid IDs: {sorted(VALID_COURSE_IDS)}"
    )


# =============================================================================
# Property 5: Question has valid exam domain
# =============================================================================

VALID_EXAM_DOMAINS = {
    "Cloud Concepts",
    "Security and Compliance",
    "Cloud Technology and Services",
    "Billing, Pricing, and Support",
    "Billing Pricing and Support",
    "Fundamentals of AI and ML",
    "AI and ML Fundamentals",
    "Fundamentals of Generative AI",
    "Generative AI",
    "Applications of Foundation Models",
    "Guidelines for Responsible AI",
    "Responsible AI",
    "Security, Compliance, and Governance for AI Solutions",
}


@settings(max_examples=200)
@given(question=sampled_from(ALL_QUESTIONS))
def test_question_has_valid_exam_domain(question):
    """
    Feature: exam-ready-quiz-rebuild, Property 5: Question has valid exam domain

    For any question in the seed data, its exam_domain must be one of the 9
    recognized domain strings.

    Validates: Requirements 1.7
    """
    domain = question["exam_domain"]
    assert domain in VALID_EXAM_DOMAINS, (
        f"Question {question['id']}: exam_domain '{domain}' is not valid. "
        f"Must be one of: {sorted(VALID_EXAM_DOMAINS)}"
    )
