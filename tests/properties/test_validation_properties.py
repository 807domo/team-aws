"""
問題バリデーションのプロパティベーステスト

Property 1: Question validation accepts valid and rejects invalid
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.domain.models import Difficulty
from app.domain.question_validator import validate_question


# =============================================================================
# Property 1: Question validation accepts valid and rejects invalid
# =============================================================================

# Valid difficulty values
VALID_DIFFICULTIES = [d.value for d in Difficulty]  # ["基礎", "中級", "上級"]

# Strategy for non-empty strings (valid text fields)
non_empty_text = st.text(min_size=1, max_size=200).filter(lambda s: s.strip() != "")

# Strategy for valid question data
valid_question_strategy = st.fixed_dictionaries(
    {
        "text": non_empty_text,
        "choice_1": non_empty_text,
        "choice_2": non_empty_text,
        "choice_3": non_empty_text,
        "choice_4": non_empty_text,
        "correct_choice_index": st.integers(min_value=0, max_value=3),
        "ehime_trivia": non_empty_text,
        "aws_ai_explanation": non_empty_text,
        "course_id": non_empty_text,
        "difficulty": st.sampled_from(VALID_DIFFICULTIES),
    }
)


@settings(max_examples=100)
@given(question_data=valid_question_strategy)
def test_valid_question_is_accepted(question_data: dict):
    """
    Feature: ehime-ai-quiz, Property 1: Question validation accepts valid and rejects invalid

    For any question data containing: non-empty question text, exactly 4 non-empty
    choices, correct_choice_index in [0,3], non-empty ehime_trivia, non-empty
    aws_ai_explanation, valid course_id, and valid difficulty,
    the validation SHALL accept it.

    Validates: Requirements 2.1, 5.4, 8.3, 9.1, 9.3, 9.6
    """
    result = validate_question(question_data)

    assert result.is_valid, (
        f"Valid question data was rejected. Errors: {result.errors}"
    )
    assert result.errors == []


# --- Strategies for invalid question data ---

# Strategy for empty/whitespace-only strings
empty_or_whitespace = st.sampled_from(["", "   ", "\t", "\n"])

# Invalid values for text fields (empty, whitespace, non-string)
invalid_text_values = st.one_of(
    empty_or_whitespace,
    st.just(None),
    st.integers(),
)


@settings(max_examples=100)
@given(
    valid_data=valid_question_strategy,
    invalid_text=invalid_text_values,
)
def test_invalid_question_text_is_rejected(valid_data: dict, invalid_text):
    """
    Feature: ehime-ai-quiz, Property 1: Question validation accepts valid and rejects invalid

    Question data with invalid text field SHALL be rejected and
    the error SHALL identify the 'text' field.

    Validates: Requirements 2.1, 5.4, 8.3, 9.1, 9.3, 9.6
    """
    question_data = {**valid_data, "text": invalid_text}
    result = validate_question(question_data)

    assert not result.is_valid
    assert any("text" in error for error in result.errors)


@settings(max_examples=100)
@given(
    valid_data=valid_question_strategy,
    invalid_choice=invalid_text_values,
    choice_field=st.sampled_from(["choice_1", "choice_2", "choice_3", "choice_4"]),
)
def test_invalid_choice_is_rejected(valid_data: dict, invalid_choice, choice_field: str):
    """
    Feature: ehime-ai-quiz, Property 1: Question validation accepts valid and rejects invalid

    Question data with any invalid choice field SHALL be rejected and
    the error SHALL identify the specific choice field.

    Validates: Requirements 2.1, 5.4, 8.3, 9.1, 9.3, 9.6
    """
    question_data = {**valid_data, choice_field: invalid_choice}
    result = validate_question(question_data)

    assert not result.is_valid
    assert any(choice_field in error for error in result.errors)


@settings(max_examples=100)
@given(
    valid_data=valid_question_strategy,
    invalid_index=st.one_of(
        st.integers(max_value=-1),
        st.integers(min_value=4),
        st.just(None),
        st.text(min_size=1, max_size=5),
    ),
)
def test_invalid_correct_choice_index_is_rejected(valid_data: dict, invalid_index):
    """
    Feature: ehime-ai-quiz, Property 1: Question validation accepts valid and rejects invalid

    Question data with correct_choice_index outside [0,3] or non-integer
    SHALL be rejected and the error SHALL identify 'correct_choice_index'.

    Validates: Requirements 2.1, 5.4, 8.3, 9.1, 9.3, 9.6
    """
    question_data = {**valid_data, "correct_choice_index": invalid_index}
    result = validate_question(question_data)

    assert not result.is_valid
    assert any("correct_choice_index" in error for error in result.errors)


@settings(max_examples=100)
@given(
    valid_data=valid_question_strategy,
    invalid_difficulty=st.text(min_size=1, max_size=10).filter(
        lambda s: s not in VALID_DIFFICULTIES
    ),
)
def test_invalid_difficulty_is_rejected(valid_data: dict, invalid_difficulty: str):
    """
    Feature: ehime-ai-quiz, Property 1: Question validation accepts valid and rejects invalid

    Question data with invalid difficulty (not 基礎/中級/上級)
    SHALL be rejected and the error SHALL identify 'difficulty'.

    Validates: Requirements 2.1, 5.4, 8.3, 9.1, 9.3, 9.6
    """
    question_data = {**valid_data, "difficulty": invalid_difficulty}
    result = validate_question(question_data)

    assert not result.is_valid
    assert any("difficulty" in error for error in result.errors)


@settings(max_examples=100)
@given(
    valid_data=valid_question_strategy,
    invalid_trivia=invalid_text_values,
)
def test_invalid_ehime_trivia_is_rejected(valid_data: dict, invalid_trivia):
    """
    Feature: ehime-ai-quiz, Property 1: Question validation accepts valid and rejects invalid

    Question data with invalid ehime_trivia SHALL be rejected and
    the error SHALL identify 'ehime_trivia'.

    Validates: Requirements 2.1, 5.4, 8.3, 9.1, 9.3, 9.6
    """
    question_data = {**valid_data, "ehime_trivia": invalid_trivia}
    result = validate_question(question_data)

    assert not result.is_valid
    assert any("ehime_trivia" in error for error in result.errors)


@settings(max_examples=100)
@given(
    valid_data=valid_question_strategy,
    invalid_explanation=invalid_text_values,
)
def test_invalid_aws_ai_explanation_is_rejected(valid_data: dict, invalid_explanation):
    """
    Feature: ehime-ai-quiz, Property 1: Question validation accepts valid and rejects invalid

    Question data with invalid aws_ai_explanation SHALL be rejected and
    the error SHALL identify 'aws_ai_explanation'.

    Validates: Requirements 2.1, 5.4, 8.3, 9.1, 9.3, 9.6
    """
    question_data = {**valid_data, "aws_ai_explanation": invalid_explanation}
    result = validate_question(question_data)

    assert not result.is_valid
    assert any("aws_ai_explanation" in error for error in result.errors)


@settings(max_examples=100)
@given(
    valid_data=valid_question_strategy,
    invalid_course_id=invalid_text_values,
)
def test_invalid_course_id_is_rejected(valid_data: dict, invalid_course_id):
    """
    Feature: ehime-ai-quiz, Property 1: Question validation accepts valid and rejects invalid

    Question data with invalid course_id SHALL be rejected and
    the error SHALL identify 'course_id'.

    Validates: Requirements 2.1, 5.4, 8.3, 9.1, 9.3, 9.6
    """
    question_data = {**valid_data, "course_id": invalid_course_id}
    result = validate_question(question_data)

    assert not result.is_valid
    assert any("course_id" in error for error in result.errors)


# =============================================================================
# Property 2: Question data round-trip preservation
# Property 3: Question ID uniqueness
# =============================================================================

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.data.database import Base
from app.data.question_repository import QuestionRepository
from app.data.models import CourseModel


def _create_in_memory_session():
    """テスト用のインメモリSQLiteセッションを作成する。"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()

    # テスト用コースを挿入
    course = CourseModel(
        id="test-course-001",
        name="テストコース",
        region="中予",
        difficulty="基礎",
        description="テスト用コース",
    )
    session.add(course)
    session.commit()
    return session


# Strategy for valid question data used in repository tests
valid_question_for_repo = st.fixed_dictionaries(
    {
        "text": non_empty_text,
        "choice_1": non_empty_text,
        "choice_2": non_empty_text,
        "choice_3": non_empty_text,
        "choice_4": non_empty_text,
        "correct_choice_index": st.integers(min_value=0, max_value=3),
        "ehime_trivia": non_empty_text,
        "aws_ai_explanation": non_empty_text,
        "course_id": st.just("test-course-001"),
        "difficulty": st.sampled_from(VALID_DIFFICULTIES),
        "exam_domain": st.sampled_from([
            "Cloud Concepts",
            "Security and Compliance",
            "Cloud Technology and Services",
            "AI and ML Fundamentals",
        ]),
    }
)


@settings(max_examples=100)
@given(question_data=valid_question_for_repo)
def test_question_round_trip_preservation(question_data: dict):
    """
    Feature: ehime-ai-quiz, Property 2: Question data round-trip preservation

    For any valid question stored in the system, retrieving that question by
    its ID SHALL return all original fields with values equal to the original input.

    Validates: Requirements 9.4
    """
    session = _create_in_memory_session()
    try:
        repo = QuestionRepository(session)

        # 一意のIDを付与
        question_data_with_id = {**question_data, "id": str(uuid.uuid4())}

        # 保存
        created = repo.create_question(question_data_with_id)

        # IDで取得
        retrieved = repo.get_question_by_id(created.id)

        # ラウンドトリップ検証
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.text == question_data["text"]
        assert retrieved.choice_1 == question_data["choice_1"]
        assert retrieved.choice_2 == question_data["choice_2"]
        assert retrieved.choice_3 == question_data["choice_3"]
        assert retrieved.choice_4 == question_data["choice_4"]
        assert retrieved.correct_choice_index == question_data["correct_choice_index"]
        assert retrieved.ehime_trivia == question_data["ehime_trivia"]
        assert retrieved.aws_ai_explanation == question_data["aws_ai_explanation"]
        assert retrieved.course_id == question_data["course_id"]
        assert retrieved.difficulty.value == question_data["difficulty"]
    finally:
        session.close()


@settings(max_examples=100)
@given(
    question_data_list=st.lists(
        valid_question_for_repo, min_size=2, max_size=10
    )
)
def test_question_id_uniqueness(question_data_list: list[dict]):
    """
    Feature: ehime-ai-quiz, Property 3: Question ID uniqueness

    For any set of questions created in the system, all assigned question IDs
    SHALL be distinct from one another.

    Validates: Requirements 9.5
    """
    session = _create_in_memory_session()
    try:
        repo = QuestionRepository(session)
        created_ids: list[str] = []

        for qdata in question_data_list:
            # IDを自動生成させる（idキーを含めない）
            created = repo.create_question(qdata)
            created_ids.append(created.id)

        # 全IDが一意であることを検証
        assert len(created_ids) == len(set(created_ids)), (
            f"重複IDが検出されました: {created_ids}"
        )
    finally:
        session.close()
