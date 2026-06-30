"""
称号マスタモジュールのプロパティベーステスト

Property 5: 称号マッピングの全射性と正確性
Property 6: 称号マスタ入力バリデーション

Validates: Requirements 4.1, 4.3, 4.4
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.domain.title_master import get_title, TITLE_MAPPING, MAX_TITLE


# 既知の称号セット
VALID_TITLES = {
    "伊予の迷い人",
    "愛媛の駆け出しAI研究者",
    "道後を極めしAIエンジニア",
    "伝説の愛媛AIマスター",
}


# =============================================================================
# Property 5: 称号マッピングの全射性と正確性
# =============================================================================


@settings(max_examples=100)
@given(level=st.integers(min_value=1, max_value=99))
def test_get_title_returns_valid_title_for_any_level(level: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 5: 称号マッピングの全射性と正確性

    For any valid level (1-99), get_title SHALL return a non-empty string
    from the known set of titles.

    **Validates: Requirements 4.1, 4.3**
    """
    result = get_title(level)

    assert isinstance(result, str), (
        f"get_title({level}) returned {type(result)}, expected str"
    )
    assert len(result) > 0, (
        f"get_title({level}) returned empty string"
    )
    assert result in VALID_TITLES, (
        f"get_title({level}) = '{result}', expected one of {VALID_TITLES}"
    )


@settings(max_examples=100)
@given(level=st.integers(min_value=1, max_value=99))
def test_get_title_mapping_accuracy(level: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 5: 称号マッピングの全射性と正確性

    For any valid level (1-99), get_title SHALL return the correct title
    according to the mapping:
    - Level 1-2: "伊予の迷い人"
    - Level 3-5: "愛媛の駆け出しAI研究者"
    - Level 6-9: "道後を極めしAIエンジニア"
    - Level 10+: "伝説の愛媛AIマスター"

    **Validates: Requirements 4.1, 4.3**
    """
    result = get_title(level)

    if level <= 2:
        expected = "伊予の迷い人"
    elif level <= 5:
        expected = "愛媛の駆け出しAI研究者"
    elif level <= 9:
        expected = "道後を極めしAIエンジニア"
    else:
        expected = "伝説の愛媛AIマスター"

    assert result == expected, (
        f"get_title({level}) = '{result}', expected '{expected}'"
    )


@settings(max_examples=100)
@given(level=st.integers(min_value=1, max_value=99))
def test_get_title_deterministic(level: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 5: 称号マッピングの全射性と正確性

    The mapping is consistent: same level always gives the same title.

    **Validates: Requirements 4.1, 4.3**
    """
    result1 = get_title(level)
    result2 = get_title(level)

    assert result1 == result2, (
        f"get_title({level}) is non-deterministic: '{result1}' != '{result2}'"
    )


# =============================================================================
# Property 6: 称号マスタ入力バリデーション
# =============================================================================


@settings(max_examples=100)
@given(level=st.integers(max_value=0))
def test_get_title_rejects_level_below_one(level: int):
    """
    Feature: ehime-rpg-map-topscreen, Property 6: 称号マスタ入力バリデーション

    For any level < 1, get_title SHALL raise ValueError.

    **Validates: Requirements 4.4**
    """
    with pytest.raises(ValueError):
        get_title(level)


@settings(max_examples=100)
@given(value=st.floats(allow_nan=True, allow_infinity=True))
def test_get_title_rejects_float(value: float):
    """
    Feature: ehime-rpg-map-topscreen, Property 6: 称号マスタ入力バリデーション

    For any float value (non-integer), get_title SHALL raise ValueError.

    **Validates: Requirements 4.4**
    """
    with pytest.raises((ValueError, TypeError)):
        get_title(value)


@settings(max_examples=100)
@given(value=st.booleans())
def test_get_title_rejects_bool(value: bool):
    """
    Feature: ehime-rpg-map-topscreen, Property 6: 称号マスタ入力バリデーション

    For any boolean value, get_title SHALL raise ValueError.

    **Validates: Requirements 4.4**
    """
    with pytest.raises(ValueError):
        get_title(value)


def test_get_title_rejects_none():
    """
    Feature: ehime-rpg-map-topscreen, Property 6: 称号マスタ入力バリデーション

    None input SHALL raise ValueError.

    **Validates: Requirements 4.4**
    """
    with pytest.raises((ValueError, TypeError)):
        get_title(None)
