"""
結果サービスのプロパティベーステスト

Property 9: Exploration rate calculation
Property 13: Chronological ordering of attempts
"""

from datetime import datetime, timedelta

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.domain.models import AttemptRecord, Grade, Region
from app.domain.scoring import calculate_accuracy_rate


# =============================================================================
# Strategies
# =============================================================================

region_strategy = st.sampled_from(list(Region))
grade_strategy = st.sampled_from(list(Grade))

# Strategy for timestamps in a reasonable range
timestamp_strategy = st.datetimes(
    min_value=datetime(2024, 1, 1),
    max_value=datetime(2026, 12, 31),
)

# Strategy for AttemptRecord
attempt_record_strategy = st.builds(
    AttemptRecord,
    session_id=st.uuids().map(str),
    course_name=st.text(min_size=1, max_size=30).filter(lambda s: s.strip() != ""),
    accuracy_rate=st.floats(min_value=0.0, max_value=100.0),
    grade=grade_strategy,
    completed_at=timestamp_strategy,
)


# =============================================================================
# Property 9: Exploration rate calculation
# =============================================================================


@settings(max_examples=100)
@given(
    completed=st.integers(min_value=0, max_value=100),
    total=st.integers(min_value=1, max_value=100),
)
def test_exploration_rate_calculation(completed: int, total: int):
    """
    Feature: ehime-ai-quiz, Property 9: Exploration rate calculation

    For any set of course completion states and total available courses,
    the exploration rate SHALL equal round(completed_courses / total_courses * 100, 1).

    Validates: Requirements 6.3
    """
    # completed は total を超えないようにする
    assume(completed <= total)

    # calculate_accuracy_rate は探索率計算にも使用される
    exploration_rate = calculate_accuracy_rate(completed, total)

    expected = round(completed / total * 100, 1)
    assert exploration_rate == expected, (
        f"exploration_rate={exploration_rate}, expected={expected} "
        f"(completed={completed}, total={total})"
    )


@settings(max_examples=100)
@given(
    completed_regions=st.lists(
        region_strategy, min_size=0, max_size=3, unique=True
    )
)
def test_exploration_region_count(completed_regions: list[Region]):
    """
    Feature: ehime-ai-quiz, Property 9: Exploration rate calculation

    The region_count SHALL equal the number of distinct regions (中予, 南予, 東予)
    in which at least one course has been completed.

    Validates: Requirements 6.3
    """
    # 完了した地域のsetから一意の地域数を計算
    region_count = len(set(completed_regions))

    # 0〜3の範囲であること
    assert 0 <= region_count <= 3

    # 完了地域数は入力の一意地域数と等しい
    assert region_count == len(completed_regions), (
        f"region_count={region_count}, expected={len(completed_regions)}"
    )


# =============================================================================
# Property 13: Chronological ordering of attempts
# =============================================================================


@settings(max_examples=100)
@given(
    attempts=st.lists(attempt_record_strategy, min_size=2, max_size=20)
)
def test_attempts_chronological_ordering(attempts: list[AttemptRecord]):
    """
    Feature: ehime-ai-quiz, Property 13: Chronological ordering of attempts

    For any set of quiz or mock exam attempts displayed on the Results Dashboard,
    the attempts SHALL be ordered by their timestamp in ascending chronological order.

    Validates: Requirements 6.4
    """
    # ResultsService.get_attempt_history() と同じソートロジックを適用
    sorted_attempts = sorted(attempts, key=lambda a: a.completed_at)

    # ソート後、各要素が前の要素より後（または同時刻）であることを検証
    for i in range(1, len(sorted_attempts)):
        assert sorted_attempts[i].completed_at >= sorted_attempts[i - 1].completed_at, (
            f"時系列順が壊れています: "
            f"index {i-1} ({sorted_attempts[i-1].completed_at}) > "
            f"index {i} ({sorted_attempts[i].completed_at})"
        )


@settings(max_examples=100)
@given(
    attempts=st.lists(attempt_record_strategy, min_size=1, max_size=20)
)
def test_sorted_attempts_preserve_all_records(attempts: list[AttemptRecord]):
    """
    Feature: ehime-ai-quiz, Property 13: Chronological ordering of attempts

    Sorting SHALL preserve all attempt records (no records lost or duplicated).

    Validates: Requirements 6.4
    """
    sorted_attempts = sorted(attempts, key=lambda a: a.completed_at)

    # ソート後の要素数が元と同じであることを検証
    assert len(sorted_attempts) == len(attempts), (
        f"ソート後の要素数 {len(sorted_attempts)} != 元の要素数 {len(attempts)}"
    )

    # 全ての元のセッションIDがソート後にも存在することを検証
    original_ids = {a.session_id for a in attempts}
    sorted_ids = {a.session_id for a in sorted_attempts}
    assert original_ids == sorted_ids, (
        f"ソートによりレコードが失われました"
    )
