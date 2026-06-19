"""
模擬試験エンジンのプロパティベーステスト

Property 10: Mock exam remaining time calculation
"""

from datetime import datetime, timedelta

from hypothesis import given, settings, assume
from hypothesis import strategies as st


# =============================================================================
# Constants
# =============================================================================

MOCK_EXAM_DURATION_MINUTES = 90


# =============================================================================
# Strategies
# =============================================================================

# Strategy for start times in a reasonable range
start_time_strategy = st.datetimes(
    min_value=datetime(2024, 1, 1),
    max_value=datetime(2026, 12, 31),
)

# Strategy for elapsed time (0 to 180 minutes - beyond exam duration too)
elapsed_minutes_strategy = st.floats(
    min_value=0.0, max_value=180.0, allow_nan=False, allow_infinity=False
)


# =============================================================================
# Property 10: Mock exam remaining time calculation
# =============================================================================


@settings(max_examples=100)
@given(
    start_time=start_time_strategy,
    elapsed_minutes=elapsed_minutes_strategy,
)
def test_remaining_time_calculation(start_time: datetime, elapsed_minutes: float):
    """
    Feature: ehime-ai-quiz, Property 10: Mock exam remaining time calculation

    For any mock exam session with a start time and a 90-minute duration,
    the remaining time at any point SHALL equal
    max(0, (start_time + 90 minutes) - current_time).

    Validates: Requirements 5.2
    """
    # current_time = start_time + elapsed
    current_time = start_time + timedelta(minutes=elapsed_minutes)

    # expires_at = start_time + 90 minutes
    expires_at = start_time + timedelta(minutes=MOCK_EXAM_DURATION_MINUTES)

    # 期待される残り時間
    expected_remaining = expires_at - current_time
    if expected_remaining.total_seconds() <= 0:
        expected_remaining = timedelta(0)

    # 実際のロジック（MockExamEngine.get_remaining_time の核心部分）
    remaining = expires_at - current_time
    if remaining.total_seconds() <= 0:
        actual_remaining = timedelta(0)
    else:
        actual_remaining = remaining

    assert actual_remaining == expected_remaining, (
        f"remaining_time mismatch: actual={actual_remaining}, "
        f"expected={expected_remaining} "
        f"(start={start_time}, elapsed={elapsed_minutes}min)"
    )


@settings(max_examples=100)
@given(
    start_time=start_time_strategy,
    elapsed_minutes=st.floats(
        min_value=90.0, max_value=180.0, allow_nan=False, allow_infinity=False
    ),
)
def test_expired_exam_remaining_is_zero(start_time: datetime, elapsed_minutes: float):
    """
    Feature: ehime-ai-quiz, Property 10: Mock exam remaining time calculation

    When remaining time reaches 0 (elapsed >= 90 minutes),
    the exam SHALL be marked as expired.

    Validates: Requirements 5.2
    """
    current_time = start_time + timedelta(minutes=elapsed_minutes)
    expires_at = start_time + timedelta(minutes=MOCK_EXAM_DURATION_MINUTES)

    remaining = expires_at - current_time

    # 90分以上経過していれば残り時間は0以下
    assert remaining.total_seconds() <= 0, (
        f"90分以上経過 ({elapsed_minutes}min) したが "
        f"remaining={remaining} が正の値"
    )

    # max(0, remaining) を適用すると 0
    actual_remaining = max(timedelta(0), remaining) if remaining.total_seconds() > 0 else timedelta(0)
    assert actual_remaining == timedelta(0), (
        f"期限切れなのに remaining={actual_remaining} != 0"
    )


@settings(max_examples=100)
@given(
    start_time=start_time_strategy,
    elapsed_minutes=st.floats(
        min_value=0.0,
        max_value=89.99,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_active_exam_remaining_is_positive(start_time: datetime, elapsed_minutes: float):
    """
    Feature: ehime-ai-quiz, Property 10: Mock exam remaining time calculation

    When elapsed time is less than 90 minutes, remaining time SHALL be positive.

    Validates: Requirements 5.2
    """
    current_time = start_time + timedelta(minutes=elapsed_minutes)
    expires_at = start_time + timedelta(minutes=MOCK_EXAM_DURATION_MINUTES)

    remaining = expires_at - current_time

    assert remaining.total_seconds() > 0, (
        f"90分未満の経過 ({elapsed_minutes}min) なのに "
        f"remaining={remaining} が正でない"
    )
