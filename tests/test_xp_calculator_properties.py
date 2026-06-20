"""
XP算出モジュールのプロパティベーステスト

Property 1: XP計算の正確性
Property 2: XP非負不変量

Validates: Requirements 2.1, 2.2, 2.3, 2.6
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.domain.xp_calculator import (
    XP_PER_CORRECT_ANSWER,
    PERFECT_COURSE_BONUS,
    add_xp,
    calculate_xp_award,
)


# =============================================================================
# Property 1: XP計算の正確性
# =============================================================================


@settings(max_examples=100)
@given(
    total_count=st.integers(min_value=1, max_value=1000),
    data=st.data(),
)
def test_xp_award_accuracy(total_count: int, data):
    """
    Feature: ehime-rpg-map-topscreen, Property 1: XP計算の正確性

    For any valid correct_count (0 <= correct_count <= total_count) and
    total_count > 0, calculate_xp_award SHALL return correct_count * 10
    when correct_count < total_count, and correct_count * 10 + 100 when
    correct_count == total_count.

    **Validates: Requirements 2.1, 2.2, 2.3**
    """
    correct_count = data.draw(
        st.integers(min_value=0, max_value=total_count),
        label="correct_count",
    )

    result = calculate_xp_award(correct_count, total_count)

    expected_base = correct_count * XP_PER_CORRECT_ANSWER
    if correct_count == total_count and total_count > 0:
        expected = expected_base + PERFECT_COURSE_BONUS
    else:
        expected = expected_base

    assert result == expected, (
        f"calculate_xp_award({correct_count}, {total_count}) = {result}, "
        f"expected {expected}"
    )


@settings(max_examples=100)
@given(
    total_count=st.integers(min_value=0, max_value=1000),
    data=st.data(),
)
def test_xp_award_non_perfect_no_bonus(total_count: int, data):
    """
    Feature: ehime-rpg-map-topscreen, Property 1: XP計算の正確性

    When correct_count < total_count, no bonus SHALL be awarded.
    The result SHALL equal correct_count * 10.

    **Validates: Requirements 2.1, 2.3**
    """
    if total_count == 0:
        # total_count=0 means no questions, correct_count must also be 0
        correct_count = 0
    else:
        correct_count = data.draw(
            st.integers(min_value=0, max_value=total_count - 1),
            label="correct_count",
        )

    result = calculate_xp_award(correct_count, total_count)

    expected = correct_count * XP_PER_CORRECT_ANSWER
    assert result == expected, (
        f"Non-perfect: calculate_xp_award({correct_count}, {total_count}) = "
        f"{result}, expected {expected}"
    )


@settings(max_examples=100)
@given(total_count=st.integers(min_value=1, max_value=1000))
def test_xp_award_perfect_bonus(total_count: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 1: XP計算の正確性

    When correct_count == total_count and total_count > 0,
    the result SHALL include the 100 XP perfect bonus.

    **Validates: Requirements 2.1, 2.2**
    """
    result = calculate_xp_award(total_count, total_count)

    expected = total_count * XP_PER_CORRECT_ANSWER + PERFECT_COURSE_BONUS
    assert result == expected, (
        f"Perfect: calculate_xp_award({total_count}, {total_count}) = "
        f"{result}, expected {expected}"
    )


# =============================================================================
# Property 2: XP非負不変量
# =============================================================================


@settings(max_examples=100)
@given(
    current_xp=st.integers(min_value=0, max_value=10_000_000),
    award=st.integers(min_value=0, max_value=10_000_000),
)
def test_add_xp_non_negative_invariant(current_xp: int, award: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 2: XP非負不変量

    For any non-negative current_xp and non-negative award,
    add_xp SHALL return a non-negative value equal to current_xp + award.

    **Validates: Requirements 2.6**
    """
    result = add_xp(current_xp, award)

    assert result >= 0, f"add_xp({current_xp}, {award}) = {result}, expected >= 0"
    assert result == current_xp + award, (
        f"add_xp({current_xp}, {award}) = {result}, "
        f"expected {current_xp + award}"
    )


@settings(max_examples=100)
@given(
    current_xp=st.integers(min_value=0, max_value=10_000_000),
    award=st.integers(min_value=0, max_value=10_000_000),
)
def test_add_xp_result_gte_current(current_xp: int, award: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 2: XP非負不変量

    add_xp SHALL always return a value >= current_xp for non-negative inputs.

    **Validates: Requirements 2.6**
    """
    result = add_xp(current_xp, award)

    assert result >= current_xp, (
        f"add_xp({current_xp}, {award}) = {result}, expected >= {current_xp}"
    )


@settings(max_examples=100)
@given(
    current_xp=st.integers(min_value=-10_000_000, max_value=-1),
    award=st.integers(min_value=0, max_value=10_000_000),
)
def test_add_xp_rejects_negative_current_xp(current_xp: int, award: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 2: XP非負不変量

    add_xp SHALL raise ValueError when current_xp is negative.

    **Validates: Requirements 2.6**
    """
    with pytest.raises(ValueError):
        add_xp(current_xp, award)


@settings(max_examples=100)
@given(
    current_xp=st.integers(min_value=0, max_value=10_000_000),
    award=st.integers(min_value=-10_000_000, max_value=-1),
)
def test_add_xp_rejects_negative_award(current_xp: int, award: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 2: XP非負不変量

    add_xp SHALL raise ValueError when award is negative.

    **Validates: Requirements 2.6**
    """
    with pytest.raises(ValueError):
        add_xp(current_xp, award)
