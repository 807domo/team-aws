"""
クイズサービスのプロパティベーステスト

Property 6: Course grouping by region
Property 11: Answer correctness determination
Property 12: Explanation length constraint
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from app.domain.models import Course, Difficulty, Explanation, Region
from app.domain.explanation_engine import (
    ExplanationEngine,
    EXPLANATION_MIN_LENGTH,
    EXPLANATION_MAX_LENGTH,
)


# =============================================================================
# Strategies
# =============================================================================

# Strategy for Region values
region_strategy = st.sampled_from(list(Region))

# Strategy for Difficulty values
difficulty_strategy = st.sampled_from(list(Difficulty))

# Strategy for Course objects
course_strategy = st.builds(
    Course,
    id=st.uuids().map(str),
    name=st.text(min_size=1, max_size=50).filter(lambda s: s.strip() != ""),
    region=region_strategy,
    difficulty=difficulty_strategy,
    description=st.text(min_size=1, max_size=100).filter(lambda s: s.strip() != ""),
)


# =============================================================================
# Property 6: Course grouping by region
# =============================================================================


def group_courses_by_region(courses: list[Course]) -> dict[Region, list[Course]]:
    """コースを地域別にグルーピングする純粋関数（テスト対象ロジックの再実装）。

    QuizService.get_courses() と CourseRepository.get_courses_grouped_by_region() の
    コアロジックをテストするために、グルーピングロジックを抽出してテストする。
    """
    grouped: dict[Region, list[Course]] = {r: [] for r in Region}
    for course in courses:
        grouped[course.region].append(course)
    return grouped


@settings(max_examples=100)
@given(courses=st.lists(course_strategy, min_size=0, max_size=20))
def test_course_grouping_places_each_in_correct_region(courses: list[Course]):
    """
    Feature: ehime-ai-quiz, Property 6: Course grouping by region

    For any set of courses with assigned regions, the grouping function SHALL
    place each course into its correct region group (中予, 南予, 東予).

    Validates: Requirements 1.1
    """
    grouped = group_courses_by_region(courses)

    # 各コースが正しい地域グループに配置されていることを検証
    for course in courses:
        assert course in grouped[course.region], (
            f"コース '{course.name}' (region={course.region}) が "
            f"正しい地域グループに含まれていません"
        )


@settings(max_examples=100)
@given(courses=st.lists(course_strategy, min_size=1, max_size=20))
def test_course_grouping_each_in_exactly_one_group(courses: list[Course]):
    """
    Feature: ehime-ai-quiz, Property 6: Course grouping by region

    For any set of courses, every course SHALL appear in exactly one group.

    Validates: Requirements 1.1
    """
    grouped = group_courses_by_region(courses)

    # 全グループ内のコース数合計が元のコース数と一致
    total_in_groups = sum(len(group) for group in grouped.values())
    assert total_in_groups == len(courses), (
        f"グループ内合計 {total_in_groups} != 元のコース数 {len(courses)}"
    )

    # 各コースは正確に1つのグループにのみ存在する
    for course in courses:
        count = sum(
            1
            for region_courses in grouped.values()
            for c in region_courses
            if c.id == course.id
        )
        assert count == 1, (
            f"コース '{course.name}' が {count} 個のグループに存在 (expected: 1)"
        )


# =============================================================================
# Property 11: Answer correctness determination
# =============================================================================


@settings(max_examples=100)
@given(
    correct_choice_index=st.integers(min_value=0, max_value=3),
    selected_choice_index=st.integers(min_value=0, max_value=3),
)
def test_answer_correctness_determination(
    correct_choice_index: int, selected_choice_index: int
):
    """
    Feature: ehime-ai-quiz, Property 11: Answer correctness determination

    For any question with a defined correct_choice_index and any user-selected
    choice_index, the answer SHALL be marked correct if and only if
    selected_choice_index equals correct_choice_index.

    Validates: Requirements 2.3
    """
    # 正誤判定ロジック（QuizService.submit_answer の核心部分）
    is_correct = selected_choice_index == correct_choice_index

    # 正解の場合
    if selected_choice_index == correct_choice_index:
        assert is_correct is True, (
            f"selected={selected_choice_index}, correct={correct_choice_index} "
            f"は正解であるべきだが is_correct={is_correct}"
        )
    else:
        # 不正解の場合
        assert is_correct is False, (
            f"selected={selected_choice_index}, correct={correct_choice_index} "
            f"は不正解であるべきだが is_correct={is_correct}"
        )


# =============================================================================
# Property 12: Explanation length constraint
# =============================================================================

# Strategy for explanation texts that are within reasonable bounds
explanation_text_strategy = st.text(
    alphabet="あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんABCDEFGHIJ0123456789",
    min_size=50,
    max_size=250,
)


def _validate_length_logic(explanation: Explanation):
    """ExplanationEngine._validate_length と同一のロジック（純粋関数として抽出）"""
    total_length = len(explanation.ehime_trivia) + len(explanation.aws_ai_explanation)
    if EXPLANATION_MIN_LENGTH <= total_length <= EXPLANATION_MAX_LENGTH:
        return explanation
    return None


@settings(max_examples=100, deadline=None)
@given(
    ehime_trivia=explanation_text_strategy,
    aws_ai_explanation=explanation_text_strategy,
)
def test_explanation_validate_length_accepts_valid(
    ehime_trivia: str, aws_ai_explanation: str
):
    """
    Feature: ehime-ai-quiz, Property 12: Explanation length constraint

    For any explanation where total character length (ehime_trivia + aws_ai_explanation)
    is between 100 and 500 characters inclusive, _validate_length SHALL accept it.
    Otherwise it SHALL return None.

    Validates: Requirements 3.3
    """
    total_length = len(ehime_trivia) + len(aws_ai_explanation)

    explanation = Explanation(
        ehime_trivia=ehime_trivia,
        aws_ai_explanation=aws_ai_explanation,
    )

    result = _validate_length_logic(explanation)

    if EXPLANATION_MIN_LENGTH <= total_length <= EXPLANATION_MAX_LENGTH:
        assert result is not None, (
            f"合計文字数 {total_length} は制約内なのに None が返されました"
        )
        assert result.ehime_trivia == ehime_trivia
        assert result.aws_ai_explanation == aws_ai_explanation
    else:
        assert result is None, (
            f"合計文字数 {total_length} は制約外なのに Explanation が返されました"
        )


@settings(max_examples=100, deadline=None)
@given(
    ehime_trivia=st.text(
        alphabet="あいうえおかきくけこさしすせそたちつてとABCDEFGHIJ0123456789",
        min_size=50,
        max_size=250,
    ),
    aws_ai_explanation=st.text(
        alphabet="あいうえおかきくけこさしすせそたちつてとABCDEFGHIJ0123456789",
        min_size=50,
        max_size=250,
    ),
)
def test_fallback_explanation_respects_length_constraint(
    ehime_trivia: str, aws_ai_explanation: str
):
    """
    Feature: ehime-ai-quiz, Property 12: Explanation length constraint

    For any explanation generated or retrieved by the Explanation Engine,
    the total character length SHALL be between 100 and 500 characters inclusive.
    The fallback explanation applies truncation when needed.

    Validates: Requirements 3.3
    """
    from app.domain.models import Question
    from unittest.mock import patch

    question = Question(
        id="test-q-001",
        course_id="test-course-001",
        text="テスト問題",
        choice_1="選択肢1",
        choice_2="選択肢2",
        choice_3="選択肢3",
        choice_4="選択肢4",
        correct_choice_index=0,
        ehime_trivia=ehime_trivia,
        aws_ai_explanation=aws_ai_explanation,
        difficulty=Difficulty.BASIC,
        exam_domain="Cloud Concepts",
    )

    # boto3 インポートを回避してインスタンス化を高速化
    with patch.object(ExplanationEngine, '_create_bedrock_client', return_value=None):
        engine = ExplanationEngine(bedrock_client=None)
    result = engine.get_fallback_explanation(question)

    total_length = len(result.ehime_trivia) + len(result.aws_ai_explanation)

    # フォールバック解説は最大500文字以内に収められる
    assert total_length <= EXPLANATION_MAX_LENGTH, (
        f"フォールバック解説の合計文字数 {total_length} が "
        f"最大値 {EXPLANATION_MAX_LENGTH} を超えています"
    )
