"""
XP/レベル整合性のプロパティベーステスト

Property 9: XP/レベル整合性不変量
- XP付与後、レベルは決して減少しない
- XPフロー全体が一貫している（有効なレベル 1-99 を返す）

Validates: Requirements 9.5
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.domain.xp_calculator import add_xp, calculate_xp_award
from app.domain.level_calculator import calculate_level, MAX_XP


# =============================================================================
# Property 9: XP/レベル整合性不変量
# =============================================================================


@settings(max_examples=200)
@given(
    total_xp=st.integers(min_value=0, max_value=MAX_XP),
    total_count=st.integers(min_value=1, max_value=100),
    data=st.data(),
)
def test_level_never_decreases_after_xp_award(
    total_xp: int, total_count: int, data
):
    """
    Feature: ehime-rpg-map-topscreen, Property 9: XP/レベル整合性不変量

    For any starting total_xp and any valid quiz result (correct_count, total_count),
    after XP award: calculate_level(new_xp) >= calculate_level(old_xp).
    Level never decreases after gaining XP.

    **Validates: Requirements 9.5**
    """
    correct_count = data.draw(
        st.integers(min_value=0, max_value=total_count),
        label="correct_count",
    )

    old_level = calculate_level(total_xp)

    award = calculate_xp_award(correct_count, total_count)
    new_xp = add_xp(total_xp, award)
    new_level = calculate_level(new_xp)

    assert new_level >= old_level, (
        f"Level decreased after XP award! "
        f"old_xp={total_xp}, award={award}, new_xp={new_xp}, "
        f"old_level={old_level}, new_level={new_level}"
    )


@settings(max_examples=200)
@given(
    total_xp=st.integers(min_value=0, max_value=MAX_XP),
    total_count=st.integers(min_value=1, max_value=100),
    data=st.data(),
)
def test_xp_flow_produces_valid_level(total_xp: int, total_count: int, data):
    """
    Feature: ehime-rpg-map-topscreen, Property 9: XP/レベル整合性不変量

    The entire XP flow is consistent: calculate_level(add_xp(xp, calculate_xp_award(c, t)))
    gives a valid level in the range [1, 99].

    **Validates: Requirements 9.5**
    """
    correct_count = data.draw(
        st.integers(min_value=0, max_value=total_count),
        label="correct_count",
    )

    award = calculate_xp_award(correct_count, total_count)
    new_xp = add_xp(total_xp, award)
    new_level = calculate_level(new_xp)

    assert 1 <= new_level <= 99, (
        f"Level out of valid range! "
        f"total_xp={total_xp}, correct_count={correct_count}, "
        f"total_count={total_count}, award={award}, "
        f"new_xp={new_xp}, new_level={new_level}"
    )


@settings(max_examples=200)
@given(
    total_xp=st.integers(min_value=0, max_value=MAX_XP),
    award=st.integers(min_value=0, max_value=10000),
)
def test_level_monotonically_non_decreasing_with_any_award(
    total_xp: int, award: int
):
    """
    Feature: ehime-rpg-map-topscreen, Property 9: XP/レベル整合性不変量

    For any valid total_xp and any non-negative award,
    adding XP never causes the level to decrease.
    This is the fundamental monotonicity property of the level system.

    **Validates: Requirements 9.5**
    """
    old_level = calculate_level(total_xp)

    new_xp = add_xp(total_xp, award)
    new_level = calculate_level(new_xp)

    assert new_level >= old_level, (
        f"Level decreased! "
        f"total_xp={total_xp}, award={award}, new_xp={new_xp}, "
        f"old_level={old_level}, new_level={new_level}"
    )
