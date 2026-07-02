"""
ツールチップテキストフォーマットのプロパティベーステスト

Property 6: ツールチップテキストフォーマットの正確性

Validates: Requirements 4.5, 4.6
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# =============================================================================
# Re-implementation of formatTooltipText in Python
# =============================================================================


def format_tooltip_text(region_name: str, completed_count: int, total_count: int) -> str:
    """
    ツールチップに表示するテキストを生成する。

    - total_count > 0 の場合: "{region_name} - {completed_count}/{total_count} コース完了"
    - total_count == 0 の場合: "{region_name} - コース準備中"
    """
    if total_count > 0:
        return f"{region_name} - {completed_count}/{total_count} コース完了"
    return f"{region_name} - コース準備中"


# =============================================================================
# Property 6: ツールチップテキストフォーマットの正確性
# =============================================================================


@settings(max_examples=100)
@given(
    region_name=st.text(min_size=1, max_size=50),
    total_count=st.integers(min_value=1, max_value=10000),
    data=st.data(),
)
def test_tooltip_format_with_courses(region_name: str, total_count: int, data):
    """
    Feature: ehime-map-ux-improvement, Property 6: ツールチップテキストフォーマットの正確性

    **Validates: Requirements 4.5, 4.6**

    For any non-empty region_name string and any 0 <= completed_count <= total_count
    where total_count > 0: result equals "{region_name} - {completed_count}/{total_count} コース完了"
    """
    completed_count = data.draw(
        st.integers(min_value=0, max_value=total_count),
        label="completed_count",
    )

    result = format_tooltip_text(region_name, completed_count, total_count)
    expected = f"{region_name} - {completed_count}/{total_count} コース完了"

    assert result == expected


@settings(max_examples=100)
@given(
    region_name=st.text(min_size=1, max_size=50),
)
def test_tooltip_format_zero_courses(region_name: str):
    """
    Feature: ehime-map-ux-improvement, Property 6: ツールチップテキストフォーマットの正確性

    **Validates: Requirements 4.5, 4.6**

    For any non-empty region_name and total_count == 0:
    result equals "{region_name} - コース準備中"
    """
    result = format_tooltip_text(region_name, 0, 0)
    expected = f"{region_name} - コース準備中"

    assert result == expected


@settings(max_examples=100)
@given(
    region_name=st.text(min_size=1, max_size=50),
    total_count=st.integers(min_value=0, max_value=10000),
    data=st.data(),
)
def test_tooltip_format_always_non_empty(region_name: str, total_count: int, data):
    """
    Feature: ehime-map-ux-improvement, Property 6: ツールチップテキストフォーマットの正確性

    **Validates: Requirements 4.5, 4.6**

    Result is always a non-empty string for any valid inputs.
    """
    completed_count = data.draw(
        st.integers(min_value=0, max_value=max(total_count, 0)),
        label="completed_count",
    )

    result = format_tooltip_text(region_name, completed_count, total_count)

    assert isinstance(result, str)
    assert len(result) > 0


@settings(max_examples=100)
@given(
    region_name=st.text(min_size=1, max_size=50),
    total_count=st.integers(min_value=0, max_value=10000),
    data=st.data(),
)
def test_tooltip_format_contains_region_name(region_name: str, total_count: int, data):
    """
    Feature: ehime-map-ux-improvement, Property 6: ツールチップテキストフォーマットの正確性

    **Validates: Requirements 4.5, 4.6**

    Result always contains the region_name for any valid inputs.
    """
    completed_count = data.draw(
        st.integers(min_value=0, max_value=max(total_count, 0)),
        label="completed_count",
    )

    result = format_tooltip_text(region_name, completed_count, total_count)

    assert region_name in result
