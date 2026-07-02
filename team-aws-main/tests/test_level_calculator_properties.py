"""
レベル計算モジュールのプロパティベーステスト

Property 3: レベル計算ラウンドトリップ
Property 4: レベル計算入力バリデーション
Property 7: XPゲージの範囲と計算式正確性
Additional: レベル計算の単調非減少性
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.domain.level_calculator import (
    MAX_LEVEL,
    MAX_XP,
    calculate_level,
    calculate_xp_gauge,
    xp_threshold_for_level,
)


# =============================================================================
# Property 3: レベル計算ラウンドトリップ
# =============================================================================


@settings(max_examples=200)
@given(total_xp=st.integers(min_value=0, max_value=MAX_XP * 2))
def test_calculate_level_returns_valid_range(total_xp: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 3: レベル計算ラウンドトリップ

    For any total_xp in [0, MAX_XP*2], calculate_level returns a value
    between 1 and 99.

    **Validates: Requirements 3.1, 3.2, 3.3**
    """
    level = calculate_level(total_xp)
    assert 1 <= level <= MAX_LEVEL


@settings(max_examples=200)
@given(total_xp=st.integers(min_value=0, max_value=MAX_XP))
def test_calculate_level_round_trip(total_xp: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 3: レベル計算ラウンドトリップ

    For any XP value from 0 to 980,100, computing the Level from XP and then
    computing the XP threshold range for that Level SHALL always place the
    original XP within that range:
    xp_threshold_for_level(level-1)² × 100 <= total_xp < xp_threshold_for_level(level)

    For level 99 (max), the upper bound check is skipped.

    **Validates: Requirements 3.1, 3.2, 3.3**
    """
    level = calculate_level(total_xp)

    # Lower bound: threshold for current level start = (level-1)² × 100
    lower_threshold = (level - 1) * (level - 1) * 100
    assert total_xp >= lower_threshold, (
        f"XP={total_xp} is below level {level} start threshold {lower_threshold}"
    )

    # Upper bound: next level threshold = level² × 100 (for level < 99)
    if level < MAX_LEVEL:
        upper_threshold = xp_threshold_for_level(level)
        assert total_xp < upper_threshold, (
            f"XP={total_xp} should be below level {level+1} threshold {upper_threshold}"
        )


# =============================================================================
# Property 4: レベル計算入力バリデーション
# =============================================================================


@settings(max_examples=100)
@given(negative_xp=st.integers(min_value=-1_000_000, max_value=-1))
def test_calculate_level_rejects_negative(negative_xp: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 4: レベル計算入力バリデーション

    For any negative value, calculate_level SHALL raise a ValueError.

    **Validates: Requirements 3.4**
    """
    with pytest.raises(ValueError):
        calculate_level(negative_xp)


@settings(max_examples=100)
@given(float_xp=st.floats(allow_nan=False, allow_infinity=False))
def test_calculate_level_rejects_float(float_xp: float):
    """
    Feature: ehime-rpg-map-topscreen, Property 4: レベル計算入力バリデーション

    For any float value, calculate_level SHALL raise a ValueError.

    **Validates: Requirements 3.4**
    """
    with pytest.raises(ValueError):
        calculate_level(float_xp)


# =============================================================================
# Property 7: XPゲージの範囲と計算式正確性
# =============================================================================


@settings(max_examples=200)
@given(total_xp=st.integers(min_value=0, max_value=MAX_XP))
def test_xp_gauge_percentage_range(total_xp: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 7: XPゲージの範囲と計算式正確性

    For any valid total_xp and its corresponding level, calculate_xp_gauge
    returns a percentage always in [0.0, 100.0].

    **Validates: Requirements 1.2, 1.3, 1.5**
    """
    level = calculate_level(total_xp)
    gauge = calculate_xp_gauge(total_xp, level)

    assert 0.0 <= gauge["percentage"] <= 100.0, (
        f"percentage={gauge['percentage']} out of [0.0, 100.0] range "
        f"for xp={total_xp}, level={level}"
    )


@settings(max_examples=200)
@given(total_xp=st.integers(min_value=0, max_value=MAX_XP))
def test_xp_gauge_current_level_xp_non_negative(total_xp: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 7: XPゲージの範囲と計算式正確性

    For any valid total_xp and its corresponding level, current_level_xp >= 0.

    **Validates: Requirements 1.2, 1.3, 1.5**
    """
    level = calculate_level(total_xp)
    gauge = calculate_xp_gauge(total_xp, level)

    assert gauge["current_level_xp"] >= 0, (
        f"current_level_xp={gauge['current_level_xp']} is negative "
        f"for xp={total_xp}, level={level}"
    )


@settings(max_examples=200)
@given(total_xp=st.integers(min_value=0, max_value=MAX_XP))
def test_xp_gauge_required_xp_non_negative(total_xp: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 7: XPゲージの範囲と計算式正確性

    For any valid total_xp and its corresponding level, required_xp >= 0.

    **Validates: Requirements 1.2, 1.3, 1.5**
    """
    level = calculate_level(total_xp)
    gauge = calculate_xp_gauge(total_xp, level)

    assert gauge["required_xp"] >= 0, (
        f"required_xp={gauge['required_xp']} is negative "
        f"for xp={total_xp}, level={level}"
    )


@settings(max_examples=200)
@given(total_xp=st.integers(min_value=0, max_value=MAX_XP))
def test_xp_gauge_formula_accuracy(total_xp: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 7: XPゲージの範囲と計算式正確性

    For any valid total_xp and its corresponding level (below max),
    percentage is computed as:
    (total_xp - threshold(level-1)²×100) / (threshold(level)²×100 - threshold(level-1)²×100) × 100
    For max level, percentage is 100.0.

    **Validates: Requirements 1.2, 1.3, 1.5**
    """
    level = calculate_level(total_xp)
    gauge = calculate_xp_gauge(total_xp, level)

    if level >= MAX_LEVEL:
        assert gauge["percentage"] == 100.0
        assert gauge["current_level_xp"] == 0
        assert gauge["required_xp"] == 0
    else:
        level_start_xp = (level - 1) * (level - 1) * 100
        next_level_xp = level * level * 100
        expected_current = total_xp - level_start_xp
        expected_required = next_level_xp - level_start_xp
        expected_percentage = round(expected_current / expected_required * 100, 1)

        assert gauge["current_level_xp"] == expected_current
        assert gauge["required_xp"] == expected_required
        assert gauge["percentage"] == expected_percentage


# =============================================================================
# Additional Property: レベル計算の単調非減少性
# =============================================================================


@settings(max_examples=200)
@given(
    xp_lower=st.integers(min_value=0, max_value=MAX_XP),
    xp_higher=st.integers(min_value=0, max_value=MAX_XP),
)
def test_calculate_level_monotonically_non_decreasing(xp_lower: int, xp_higher: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 3: レベル計算ラウンドトリップ

    calculate_level is monotonically non-decreasing: higher xp yields same
    or higher level.

    **Validates: Requirements 3.1, 3.2**
    """
    assume(xp_lower <= xp_higher)

    level_lower = calculate_level(xp_lower)
    level_higher = calculate_level(xp_higher)

    assert level_lower <= level_higher, (
        f"Monotonicity violated: xp={xp_lower}→L{level_lower}, "
        f"xp={xp_higher}→L{level_higher}"
    )
