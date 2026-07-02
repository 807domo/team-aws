"""
進捗ステータス算出モジュールのプロパティベーステスト

Property 8: 進捗ステータスの決定性

Validates: Requirements 7.2, 7.4
"""

from datetime import datetime

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from app.domain.models import AnswerRecord
from app.domain.progress_calculator import ProgressStatus, calculate_region_progress


# =============================================================================
# Hypothesis Strategies
# =============================================================================

# コースIDジェネレータ
course_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
    min_size=1,
    max_size=10,
)

# 問題IDジェネレータ
question_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
    min_size=1,
    max_size=10,
)

# 地域名ジェネレータ
region_strategy = st.sampled_from(["CHUYO", "NANYO", "TOYO"])


@composite
def answer_record_strategy(draw, course_ids=None, question_ids=None):
    """AnswerRecord を生成するコンポジット戦略"""
    if course_ids is not None and len(course_ids) > 0:
        course_id = draw(st.sampled_from(course_ids))
    else:
        course_id = draw(course_id_strategy)

    if question_ids is not None and len(question_ids) > 0:
        question_id = draw(st.sampled_from(question_ids))
    else:
        question_id = draw(question_id_strategy)

    return AnswerRecord(
        id=draw(st.text(min_size=1, max_size=8)),
        user_id="test_user",
        question_id=question_id,
        course_id=course_id,
        selected_choice_index=draw(st.integers(min_value=0, max_value=3)),
        is_correct=draw(st.booleans()),
        answered_at=datetime.now(),
    )


@composite
def progress_scenario(draw):
    """進捗テスト用のシナリオ全体を生成する戦略

    Returns:
        tuple of (region, courses_in_region, user_answer_records, course_questions)
    """
    region = draw(region_strategy)

    # コース数を生成（0〜5）
    num_courses = draw(st.integers(min_value=0, max_value=5))
    courses_in_region = [f"course_{i}" for i in range(num_courses)]

    # コースごとの問題マッピングを生成
    course_questions = {}
    all_question_ids = []
    for course_id in courses_in_region:
        num_questions = draw(st.integers(min_value=1, max_value=5))
        questions = [f"{course_id}_q{j}" for j in range(num_questions)]
        course_questions[course_id] = questions
        all_question_ids.extend(questions)

    # 回答記録を生成（コースと問題IDを制約付きで生成）
    if courses_in_region and all_question_ids:
        num_records = draw(st.integers(min_value=0, max_value=20))
        records = []
        for _ in range(num_records):
            c_id = draw(st.sampled_from(courses_in_region))
            q_ids_for_course = course_questions[c_id]
            q_id = draw(st.sampled_from(q_ids_for_course))
            record = AnswerRecord(
                id=draw(st.text(min_size=1, max_size=8)),
                user_id="test_user",
                question_id=q_id,
                course_id=c_id,
                selected_choice_index=draw(st.integers(min_value=0, max_value=3)),
                is_correct=draw(st.booleans()),
                answered_at=datetime.now(),
            )
            records.append(record)
    else:
        records = []

    return (region, courses_in_region, records, course_questions)


# =============================================================================
# Property 8: 進捗ステータスの決定性
# =============================================================================


@settings(max_examples=200)
@given(scenario=progress_scenario())
def test_determinism_same_inputs_same_output(scenario):
    """
    Feature: ehime-rpg-map-topscreen, Property 8: 進捗ステータスの決定性

    For any region, courses, answer records, and course-question mappings,
    calling calculate_region_progress with the same inputs SHALL always
    produce the same ProgressStatus.

    **Validates: Requirements 7.2, 7.4**
    """
    region, courses_in_region, records, course_questions = scenario

    result1 = calculate_region_progress(region, courses_in_region, records, course_questions)
    result2 = calculate_region_progress(region, courses_in_region, records, course_questions)

    assert result1 == result2, (
        f"Non-deterministic: first call returned {result1}, "
        f"second call returned {result2} for same inputs"
    )


@settings(max_examples=200)
@given(scenario=progress_scenario())
def test_result_is_valid_progress_status(scenario):
    """
    Feature: ehime-rpg-map-topscreen, Property 8: 進捗ステータスの決定性

    For any valid inputs, calculate_region_progress SHALL always return
    a valid ProgressStatus enum value.

    **Validates: Requirements 7.2, 7.4**
    """
    region, courses_in_region, records, course_questions = scenario

    result = calculate_region_progress(region, courses_in_region, records, course_questions)

    assert isinstance(result, ProgressStatus), (
        f"Expected ProgressStatus, got {type(result).__name__}: {result}"
    )
    assert result in (
        ProgressStatus.NOT_STARTED,
        ProgressStatus.IN_PROGRESS,
        ProgressStatus.COMPLETE,
    )


@settings(max_examples=100)
@given(region=region_strategy)
def test_zero_courses_always_complete(region):
    """
    Feature: ehime-rpg-map-topscreen, Property 8: 進捗ステータスの決定性

    For any region with zero courses, calculate_region_progress SHALL
    always return COMPLETE.

    **Validates: Requirements 7.2, 7.4**
    """
    result = calculate_region_progress(
        region=region,
        courses_in_region=[],
        user_answer_records=[],
        course_questions={},
    )

    assert result == ProgressStatus.COMPLETE, (
        f"Zero courses region should be COMPLETE, got {result}"
    )


@settings(max_examples=100)
@given(
    region=region_strategy,
    num_courses=st.integers(min_value=1, max_value=10),
)
def test_empty_records_with_courses_always_not_started(region, num_courses):
    """
    Feature: ehime-rpg-map-topscreen, Property 8: 進捗ステータスの決定性

    For any region with one or more courses and empty answer records,
    calculate_region_progress SHALL always return NOT_STARTED.

    **Validates: Requirements 7.2, 7.4**
    """
    courses_in_region = [f"course_{i}" for i in range(num_courses)]
    course_questions = {
        cid: [f"{cid}_q0", f"{cid}_q1"] for cid in courses_in_region
    }

    result = calculate_region_progress(
        region=region,
        courses_in_region=courses_in_region,
        user_answer_records=[],
        course_questions=course_questions,
    )

    assert result == ProgressStatus.NOT_STARTED, (
        f"Region with {num_courses} courses and no records should be "
        f"NOT_STARTED, got {result}"
    )


@settings(max_examples=100)
@given(
    region=region_strategy,
    data=st.data(),
)
def test_all_correct_answers_is_complete(region, data):
    """
    Feature: ehime-rpg-map-topscreen, Property 8: 進捗ステータスの決定性

    When all courses have all questions answered correctly,
    calculate_region_progress SHALL return COMPLETE.

    **Validates: Requirements 7.2, 7.4**
    """
    num_courses = data.draw(st.integers(min_value=1, max_value=5), label="num_courses")
    courses_in_region = [f"course_{i}" for i in range(num_courses)]

    course_questions = {}
    records = []
    for course_id in courses_in_region:
        num_questions = data.draw(
            st.integers(min_value=1, max_value=5), label=f"num_q_{course_id}"
        )
        questions = [f"{course_id}_q{j}" for j in range(num_questions)]
        course_questions[course_id] = questions

        # 全問正解の回答記録を作成
        for q_id in questions:
            records.append(
                AnswerRecord(
                    id=f"rec_{course_id}_{q_id}",
                    user_id="test_user",
                    question_id=q_id,
                    course_id=course_id,
                    selected_choice_index=0,
                    is_correct=True,
                    answered_at=datetime.now(),
                )
            )

    result = calculate_region_progress(region, courses_in_region, records, course_questions)

    assert result == ProgressStatus.COMPLETE, (
        f"All correct answers should yield COMPLETE, got {result}"
    )


@settings(max_examples=100)
@given(
    region=region_strategy,
    data=st.data(),
)
def test_partial_progress_is_in_progress(region, data):
    """
    Feature: ehime-rpg-map-topscreen, Property 8: 進捗ステータスの決定性

    When some courses have answer records but not all courses have all
    questions answered correctly, calculate_region_progress SHALL return
    IN_PROGRESS.

    **Validates: Requirements 7.2, 7.4**
    """
    # 少なくとも2コース（1つ完了、1つ未完了を保証）
    num_courses = data.draw(st.integers(min_value=2, max_value=5), label="num_courses")
    courses_in_region = [f"course_{i}" for i in range(num_courses)]

    course_questions = {}
    records = []

    for i, course_id in enumerate(courses_in_region):
        num_questions = data.draw(
            st.integers(min_value=1, max_value=5), label=f"num_q_{course_id}"
        )
        questions = [f"{course_id}_q{j}" for j in range(num_questions)]
        course_questions[course_id] = questions

        if i == 0:
            # 最初のコースは全問正解
            for q_id in questions:
                records.append(
                    AnswerRecord(
                        id=f"rec_{course_id}_{q_id}",
                        user_id="test_user",
                        question_id=q_id,
                        course_id=course_id,
                        selected_choice_index=0,
                        is_correct=True,
                        answered_at=datetime.now(),
                    )
                )
        elif i == 1:
            # 2番目のコースは不正解のみ（回答記録あり、完了していない）
            records.append(
                AnswerRecord(
                    id=f"rec_{course_id}_wrong",
                    user_id="test_user",
                    question_id=questions[0],
                    course_id=course_id,
                    selected_choice_index=1,
                    is_correct=False,
                    answered_at=datetime.now(),
                )
            )
        # 残りのコースは回答記録なし

    result = calculate_region_progress(region, courses_in_region, records, course_questions)

    assert result == ProgressStatus.IN_PROGRESS, (
        f"Partial progress should yield IN_PROGRESS, got {result}"
    )
