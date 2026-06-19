"""
シードデータ品質のプロパティベーステスト

Property 1: Field length invariants per exam domain
Property 2: Validation acceptance of all seed data
Property 3: Referential integrity between questions and courses
Property 5: Question ID uniqueness and format constraints
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.data.seed_data import QUESTIONS, COURSES
from app.domain.question_validator import validate_question, VALID_EXAM_DOMAINS


# =============================================================================
# Helper: domain-specific minimum lengths for aws_ai_explanation
# =============================================================================

_AWS_EXPLANATION_MIN_LENGTHS = {
    "Cloud Concepts": 50,
    "Cloud Technology and Services": 50,
    "Billing Pricing and Support": 50,
    "Generative AI": 50,
    "Security and Compliance": 20,
    "AI and ML Fundamentals": 20,
    "Responsible AI": 30,
}

# Valid course IDs extracted from COURSES
_VALID_COURSE_IDS = {course["id"] for course in COURSES}


# =============================================================================
# Property 1: Field length invariants per exam domain
# =============================================================================


@settings(max_examples=100)
@given(idx=st.integers(min_value=0, max_value=max(len(QUESTIONS) - 1, 0)))
def test_field_length_invariants_per_exam_domain(idx: int):
    """
    Feature: aws-question-expansion, Property 1: Field length invariants per exam domain

    For any Question_Entry in the seed data, the ehime_trivia field SHALL have
    a length between 30 and 200 characters, AND the aws_ai_explanation field SHALL
    meet the minimum length requirement for its exam domain.

    Validates: Requirements 1.5, 1.6, 2.5, 2.6, 3.5, 3.6, 4.4, 4.5, 5.4, 5.5, 6.5, 6.6, 7.4, 7.5, 11.3
    """
    assume(len(QUESTIONS) > 0)
    question = QUESTIONS[idx]

    # ehime_trivia: 30-200 characters
    ehime_trivia = question["ehime_trivia"]
    assert 30 <= len(ehime_trivia) <= 200, (
        f"Question {question['id']}: ehime_trivia length {len(ehime_trivia)} "
        f"is not in range [30, 200]. Content: '{ehime_trivia[:50]}...'"
    )

    # aws_ai_explanation: domain-specific minimum length
    exam_domain = question["exam_domain"]
    aws_explanation = question["aws_ai_explanation"]
    min_length = _AWS_EXPLANATION_MIN_LENGTHS.get(exam_domain, 20)

    assert len(aws_explanation) >= min_length, (
        f"Question {question['id']}: aws_ai_explanation length {len(aws_explanation)} "
        f"is less than minimum {min_length} for domain '{exam_domain}'. "
        f"Content: '{aws_explanation[:50]}...'"
    )


# =============================================================================
# Property 2: Validation acceptance of all seed data
# =============================================================================


@settings(max_examples=100)
@given(idx=st.integers(min_value=0, max_value=max(len(QUESTIONS) - 1, 0)))
def test_validation_acceptance_of_all_seed_data(idx: int):
    """
    Feature: aws-question-expansion, Property 2: Validation acceptance of all seed data

    For any Question_Entry defined in the QUESTIONS list of the Seed_Data_Module,
    calling validate_question() SHALL return a ValidationResult with is_valid=True
    and an empty errors list.

    Validates: Requirements 9.1
    """
    assume(len(QUESTIONS) > 0)
    question = QUESTIONS[idx]

    result = validate_question(question)

    assert result.is_valid, (
        f"Question {question['id']} failed validation. Errors: {result.errors}"
    )
    assert result.errors == [], (
        f"Question {question['id']} has errors: {result.errors}"
    )


# =============================================================================
# Property 3: Referential integrity between questions and courses
# =============================================================================


@settings(max_examples=100)
@given(idx=st.integers(min_value=0, max_value=max(len(QUESTIONS) - 1, 0)))
def test_referential_integrity_course_id_exists(idx: int):
    """
    Feature: aws-question-expansion, Property 3: Referential integrity between questions and courses

    For any Question_Entry in the QUESTIONS list, its course_id value SHALL match
    the id of exactly one entry in the COURSES list.

    Validates: Requirements 8.3, 8.4
    """
    assume(len(QUESTIONS) > 0)
    question = QUESTIONS[idx]

    course_id = question["course_id"]
    assert course_id in _VALID_COURSE_IDS, (
        f"Question {question['id']} references course_id '{course_id}' "
        f"which does not exist in COURSES. Valid course IDs: {sorted(_VALID_COURSE_IDS)}"
    )


@settings(max_examples=100)
@given(
    invalid_course_id=st.text(min_size=1, max_size=64).filter(
        lambda s: s.strip() != "" and s not in _VALID_COURSE_IDS
    )
)
def test_invalid_course_id_still_passes_validator(invalid_course_id: str):
    """
    Feature: aws-question-expansion, Property 3: Referential integrity between questions and courses

    The validate_question() function does not check FK constraints for course_id
    (only checks non-empty). A question with an invalid course_id that is non-empty
    still passes validation. This documents that referential integrity is enforced
    at the data layer, not the validator level.

    Validates: Requirements 8.3, 8.4
    """
    # Build a valid question with an invalid course_id
    question_data = {
        "id": "q-test-fk-001",
        "text": "テスト問題文です",
        "choice_1": "選択肢1",
        "choice_2": "選択肢2",
        "choice_3": "選択肢3",
        "choice_4": "選択肢4",
        "correct_choice_index": 0,
        "ehime_trivia": "愛媛県のテストトリビアです",
        "aws_ai_explanation": "テスト用のAWS解説文です",
        "course_id": invalid_course_id,
        "difficulty": "基礎",
        "exam_domain": "Cloud Concepts",
    }

    result = validate_question(question_data)

    # Validator does NOT check FK constraints - it only validates non-empty string
    assert result.is_valid, (
        f"Validator unexpectedly rejected valid question with course_id '{invalid_course_id}'. "
        f"Errors: {result.errors}"
    )


# =============================================================================
# Property 5: Question ID uniqueness and format constraints
# =============================================================================


def test_question_id_uniqueness():
    """
    Feature: aws-question-expansion, Property 5: Question ID uniqueness and format constraints

    All id values across the entire QUESTIONS list SHALL be distinct from one another.

    Validates: Requirements 9.2
    """
    all_ids = [q["id"] for q in QUESTIONS]
    assert len(all_ids) == len(set(all_ids)), (
        f"Duplicate IDs found: {[qid for qid in all_ids if all_ids.count(qid) > 1]}"
    )


@settings(max_examples=100)
@given(idx=st.integers(min_value=0, max_value=max(len(QUESTIONS) - 1, 0)))
def test_question_id_format_constraints(idx: int):
    """
    Feature: aws-question-expansion, Property 5: Question ID uniqueness and format constraints

    For any Question_Entry in the QUESTIONS list, the id field SHALL be a non-empty
    string of at most 50 characters containing at least one non-whitespace character.

    Validates: Requirements 9.2
    """
    assume(len(QUESTIONS) > 0)
    question = QUESTIONS[idx]

    question_id = question["id"]

    # Must be a non-empty string
    assert isinstance(question_id, str), (
        f"Question ID is not a string: {type(question_id)}"
    )
    assert len(question_id) > 0, "Question ID is empty"

    # Must be at most 50 characters
    assert len(question_id) <= 50, (
        f"Question ID '{question_id}' exceeds 50 characters (length: {len(question_id)})"
    )

    # Must contain at least one non-whitespace character
    assert question_id.strip() != "", (
        f"Question ID '{repr(question_id)}' contains only whitespace"
    )
