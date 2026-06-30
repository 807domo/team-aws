"""
スクロール判定ロジックのプロパティベーステスト

Property 4: パネルが既に可視ならスクロールしない

Validates: Requirements 3.3
"""

from hypothesis import given, settings
from hypothesis import strategies as st


# =============================================================================
# スクロール判定ロジック (Python再実装)
# =============================================================================


def should_scroll_to_panel(panel_top: float, panel_bottom: float, viewport_height: float) -> bool:
    """Returns True if scroll is needed, False if panel is already fully visible."""
    if panel_top >= 0 and panel_bottom <= viewport_height:
        return False  # Panel fully visible, no scroll needed
    return True  # Panel not fully visible, scroll needed


# =============================================================================
# Property 4: パネルが既に可視ならスクロールしない
# =============================================================================


@settings(max_examples=200)
@given(
    viewport_height=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    data=st.data(),
)
def test_fully_visible_panel_no_scroll(viewport_height: float, data):
    """
    Feature: ehime-map-ux-improvement, Property 4: パネルが既に可視ならスクロールしない

    When panel_top >= 0 AND panel_bottom <= viewport_height (fully visible),
    should_scroll_to_panel SHALL return False.

    **Validates: Requirements 3.3**
    """
    # Generate panel_top in [0, viewport_height] and panel_bottom in [panel_top, viewport_height]
    panel_top = data.draw(
        st.floats(min_value=0.0, max_value=viewport_height, allow_nan=False, allow_infinity=False),
        label="panel_top",
    )
    panel_bottom = data.draw(
        st.floats(min_value=panel_top, max_value=viewport_height, allow_nan=False, allow_infinity=False),
        label="panel_bottom",
    )

    result = should_scroll_to_panel(panel_top, panel_bottom, viewport_height)

    assert result is False, (
        f"Panel fully visible (top={panel_top}, bottom={panel_bottom}, "
        f"viewport_height={viewport_height}) should NOT scroll, but got True"
    )


@settings(max_examples=200)
@given(
    viewport_height=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    data=st.data(),
)
def test_partially_hidden_panel_scrolls_top_above(viewport_height: float, data):
    """
    Feature: ehime-map-ux-improvement, Property 4: パネルが既に可視ならスクロールしない

    When panel_top < 0 (panel extends above viewport),
    should_scroll_to_panel SHALL return True.

    **Validates: Requirements 3.3**
    """
    # Panel top is above viewport (negative)
    panel_top = data.draw(
        st.floats(min_value=-10000.0, max_value=-0.01, allow_nan=False, allow_infinity=False),
        label="panel_top",
    )
    # Panel bottom can be anywhere below panel_top
    panel_bottom = data.draw(
        st.floats(min_value=panel_top, max_value=viewport_height * 2, allow_nan=False, allow_infinity=False),
        label="panel_bottom",
    )

    result = should_scroll_to_panel(panel_top, panel_bottom, viewport_height)

    assert result is True, (
        f"Panel with top above viewport (top={panel_top}, bottom={panel_bottom}, "
        f"viewport_height={viewport_height}) SHOULD scroll, but got False"
    )


@settings(max_examples=200)
@given(
    viewport_height=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    data=st.data(),
)
def test_partially_hidden_panel_scrolls_bottom_below(viewport_height: float, data):
    """
    Feature: ehime-map-ux-improvement, Property 4: パネルが既に可視ならスクロールしない

    When panel_bottom > viewport_height (panel extends below viewport),
    should_scroll_to_panel SHALL return True.

    **Validates: Requirements 3.3**
    """
    # Panel top is within viewport
    panel_top = data.draw(
        st.floats(min_value=0.0, max_value=viewport_height, allow_nan=False, allow_infinity=False),
        label="panel_top",
    )
    # Panel bottom extends beyond viewport
    panel_bottom = data.draw(
        st.floats(min_value=viewport_height + 0.01, max_value=viewport_height * 3, allow_nan=False, allow_infinity=False),
        label="panel_bottom",
    )

    result = should_scroll_to_panel(panel_top, panel_bottom, viewport_height)

    assert result is True, (
        f"Panel with bottom below viewport (top={panel_top}, bottom={panel_bottom}, "
        f"viewport_height={viewport_height}) SHOULD scroll, but got False"
    )


@settings(max_examples=200)
@given(
    viewport_height=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    data=st.data(),
)
def test_any_fully_within_viewport_no_scroll(viewport_height: float, data):
    """
    Feature: ehime-map-ux-improvement, Property 4: パネルが既に可視ならスクロールしない

    For any viewport_height > 0 and panel fully within viewport
    (0 <= panel_top <= panel_bottom <= viewport_height): no scroll.

    **Validates: Requirements 3.3**
    """
    # Draw two points within [0, viewport_height] and sort them
    point1 = data.draw(
        st.floats(min_value=0.0, max_value=viewport_height, allow_nan=False, allow_infinity=False),
        label="point1",
    )
    point2 = data.draw(
        st.floats(min_value=0.0, max_value=viewport_height, allow_nan=False, allow_infinity=False),
        label="point2",
    )
    panel_top = min(point1, point2)
    panel_bottom = max(point1, point2)

    result = should_scroll_to_panel(panel_top, panel_bottom, viewport_height)

    assert result is False, (
        f"Panel fully within viewport (top={panel_top}, bottom={panel_bottom}, "
        f"viewport_height={viewport_height}) should NOT scroll, but got True"
    )
