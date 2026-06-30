"""
ツールチップ位置計算のプロパティベーステスト

Property 5: ツールチップはビューポート内に収まる

**Validates: Requirements 4.3**
"""

from hypothesis import given, settings
from hypothesis import strategies as st


# =============================================================================
# Python re-implementation of computeTooltipPosition from map-interactions.js
# =============================================================================

TOOLTIP_OFFSET = 12


def compute_tooltip_position(
    cursor_x: int,
    cursor_y: int,
    tooltip_w: int,
    tooltip_h: int,
    viewport_w: int,
    viewport_h: int,
) -> dict:
    """
    Compute tooltip position ensuring it stays within viewport boundaries.

    This is a Python re-implementation of the JavaScript computeTooltipPosition
    function in app/static/js/map-interactions.js for property-based testing.
    """
    x = cursor_x + TOOLTIP_OFFSET
    y = cursor_y + TOOLTIP_OFFSET

    if x + tooltip_w > viewport_w:
        x = cursor_x - tooltip_w - TOOLTIP_OFFSET
    if y + tooltip_h > viewport_h:
        y = cursor_y - tooltip_h - TOOLTIP_OFFSET

    if x < 0:
        x = 0
    if y < 0:
        y = 0

    return {"x": x, "y": y}


# =============================================================================
# Property 5: ツールチップはビューポート内に収まる
# =============================================================================


@settings(max_examples=200)
@given(data=st.data())
def test_tooltip_stays_within_viewport(data):
    """
    Feature: ehime-map-ux-improvement, Property 5: ツールチップはビューポート内に収まる

    For any cursor position (x, y) where 0 <= x <= viewport_width and
    0 <= y <= viewport_height, and for any tooltip dimensions (w, h) where
    w > 0 and h > 0 and w <= viewport_w and h <= viewport_h,
    the computed tooltip position (tx, ty) SHALL satisfy:
    0 <= tx, tx + w <= viewport_w, 0 <= ty, ty + h <= viewport_h.

    **Validates: Requirements 4.3**
    """
    # Generate realistic viewport dimensions (minimum 100px to be meaningful)
    viewport_w = data.draw(
        st.integers(min_value=100, max_value=3840),
        label="viewport_w",
    )
    viewport_h = data.draw(
        st.integers(min_value=100, max_value=2160),
        label="viewport_h",
    )

    # Tooltip must fit within viewport (w <= viewport_w, h <= viewport_h)
    tooltip_w = data.draw(
        st.integers(min_value=1, max_value=viewport_w),
        label="tooltip_w",
    )
    tooltip_h = data.draw(
        st.integers(min_value=1, max_value=viewport_h),
        label="tooltip_h",
    )

    # Cursor position within viewport bounds
    cursor_x = data.draw(
        st.integers(min_value=0, max_value=viewport_w),
        label="cursor_x",
    )
    cursor_y = data.draw(
        st.integers(min_value=0, max_value=viewport_h),
        label="cursor_y",
    )

    result = compute_tooltip_position(
        cursor_x, cursor_y, tooltip_w, tooltip_h, viewport_w, viewport_h
    )

    tx = result["x"]
    ty = result["y"]

    # Property: tooltip left edge is within viewport
    assert tx >= 0, (
        f"Tooltip x={tx} is negative. "
        f"cursor=({cursor_x},{cursor_y}), tooltip=({tooltip_w}x{tooltip_h}), "
        f"viewport=({viewport_w}x{viewport_h})"
    )

    # Property: tooltip right edge is within viewport
    assert tx + tooltip_w <= viewport_w, (
        f"Tooltip right edge {tx + tooltip_w} exceeds viewport width {viewport_w}. "
        f"cursor=({cursor_x},{cursor_y}), tooltip=({tooltip_w}x{tooltip_h}), "
        f"viewport=({viewport_w}x{viewport_h})"
    )

    # Property: tooltip top edge is within viewport
    assert ty >= 0, (
        f"Tooltip y={ty} is negative. "
        f"cursor=({cursor_x},{cursor_y}), tooltip=({tooltip_w}x{tooltip_h}), "
        f"viewport=({viewport_w}x{viewport_h})"
    )

    # Property: tooltip bottom edge is within viewport
    assert ty + tooltip_h <= viewport_h, (
        f"Tooltip bottom edge {ty + tooltip_h} exceeds viewport height {viewport_h}. "
        f"cursor=({cursor_x},{cursor_y}), tooltip=({tooltip_w}x{tooltip_h}), "
        f"viewport=({viewport_w}x{viewport_h})"
    )


@settings(max_examples=200)
@given(data=st.data())
def test_tooltip_prefers_bottom_right_placement(data):
    """
    Feature: ehime-map-ux-improvement, Property 5: ツールチップはビューポート内に収まる

    When there is enough space to the bottom-right of the cursor,
    the tooltip SHALL be placed at (cursor_x + OFFSET, cursor_y + OFFSET).

    **Validates: Requirements 4.3**
    """
    # Generate viewport large enough to always fit tooltip to bottom-right
    viewport_w = data.draw(
        st.integers(min_value=200, max_value=3840),
        label="viewport_w",
    )
    viewport_h = data.draw(
        st.integers(min_value=200, max_value=2160),
        label="viewport_h",
    )

    # Small tooltip that can fit in many positions
    tooltip_w = data.draw(
        st.integers(min_value=1, max_value=min(100, viewport_w // 2)),
        label="tooltip_w",
    )
    tooltip_h = data.draw(
        st.integers(min_value=1, max_value=min(100, viewport_h // 2)),
        label="tooltip_h",
    )

    # Cursor positioned so that bottom-right placement fits
    max_cursor_x = viewport_w - tooltip_w - TOOLTIP_OFFSET
    max_cursor_y = viewport_h - tooltip_h - TOOLTIP_OFFSET

    if max_cursor_x < 0 or max_cursor_y < 0:
        return  # Skip if constraints can't be satisfied

    cursor_x = data.draw(
        st.integers(min_value=0, max_value=max_cursor_x),
        label="cursor_x",
    )
    cursor_y = data.draw(
        st.integers(min_value=0, max_value=max_cursor_y),
        label="cursor_y",
    )

    result = compute_tooltip_position(
        cursor_x, cursor_y, tooltip_w, tooltip_h, viewport_w, viewport_h
    )

    # When there's space, tooltip should be placed at cursor + offset
    assert result["x"] == cursor_x + TOOLTIP_OFFSET, (
        f"Expected x={cursor_x + TOOLTIP_OFFSET}, got {result['x']}. "
        f"cursor=({cursor_x},{cursor_y}), tooltip=({tooltip_w}x{tooltip_h}), "
        f"viewport=({viewport_w}x{viewport_h})"
    )
    assert result["y"] == cursor_y + TOOLTIP_OFFSET, (
        f"Expected y={cursor_y + TOOLTIP_OFFSET}, got {result['y']}. "
        f"cursor=({cursor_x},{cursor_y}), tooltip=({tooltip_w}x{tooltip_h}), "
        f"viewport=({viewport_w}x{viewport_h})"
    )
