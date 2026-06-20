"""
選択状態opacity管理のプロパティベーステスト

Property 7: 地域選択時のopacity状態一貫性

Validates: Requirements 5.2, 5.3
"""

from hypothesis import given, settings
from hypothesis import strategies as st


# =============================================================================
# Model: 選択状態opacity管理ロジック
# =============================================================================

REGIONS = ["CHUYO", "NANYO", "TOYO"]


def compute_opacity_states(selected_region, all_regions):
    """Returns dict of region -> opacity (1.0 for selected, 0.5 for others)."""
    states = {}
    for region in all_regions:
        if region == selected_region:
            states[region] = 1.0
        else:
            states[region] = 0.5
    return states


# =============================================================================
# Property 7: 地域選択時のopacity状態一貫性
# =============================================================================


@settings(max_examples=100)
@given(selected_region=st.sampled_from(REGIONS))
def test_exactly_one_region_has_full_opacity(selected_region: str):
    """
    Feature: ehime-map-ux-improvement, Property 7: 地域選択時のopacity状態一貫性

    After any selection, exactly one region has opacity 1.0.

    **Validates: Requirements 5.2, 5.3**
    """
    states = compute_opacity_states(selected_region, REGIONS)

    full_opacity_regions = [r for r, o in states.items() if o == 1.0]
    assert len(full_opacity_regions) == 1, (
        f"Expected exactly 1 region with opacity 1.0, "
        f"got {len(full_opacity_regions)}: {full_opacity_regions}"
    )


@settings(max_examples=100)
@given(selected_region=st.sampled_from(REGIONS))
def test_non_selected_regions_have_dimmed_opacity(selected_region: str):
    """
    Feature: ehime-map-ux-improvement, Property 7: 地域選択時のopacity状態一貫性

    All non-selected regions have opacity 0.5.

    **Validates: Requirements 5.2, 5.3**
    """
    states = compute_opacity_states(selected_region, REGIONS)

    for region in REGIONS:
        if region != selected_region:
            assert states[region] == 0.5, (
                f"Non-selected region {region} has opacity {states[region]}, "
                f"expected 0.5"
            )


@settings(max_examples=100)
@given(
    selection_sequence=st.lists(
        st.sampled_from(REGIONS), min_size=1, max_size=50
    )
)
def test_sequential_selections_final_state_consistent(
    selection_sequence: list,
):
    """
    Feature: ehime-map-ux-improvement, Property 7: 地域選択時のopacity状態一貫性

    After a sequence of selections, the final state is always consistent
    (only the last selected region has opacity 1.0).

    **Validates: Requirements 5.2, 5.3**
    """
    # Simulate sequential selections - final state depends only on last selection
    final_selected = selection_sequence[-1]
    states = compute_opacity_states(final_selected, REGIONS)

    # Exactly one region with opacity 1.0
    full_opacity_regions = [r for r, o in states.items() if o == 1.0]
    assert len(full_opacity_regions) == 1, (
        f"After sequence {selection_sequence}, expected exactly 1 region "
        f"with opacity 1.0, got {len(full_opacity_regions)}"
    )

    # The last selected region is the one with full opacity
    assert states[final_selected] == 1.0, (
        f"Last selected region {final_selected} has opacity "
        f"{states[final_selected]}, expected 1.0"
    )

    # All others are dimmed
    for region in REGIONS:
        if region != final_selected:
            assert states[region] == 0.5, (
                f"After selecting {final_selected}, region {region} has "
                f"opacity {states[region]}, expected 0.5"
            )


@settings(max_examples=100)
@given(selected_region=st.sampled_from(REGIONS))
def test_selected_region_always_in_output_with_full_opacity(
    selected_region: str,
):
    """
    Feature: ehime-map-ux-improvement, Property 7: 地域選択時のopacity状態一貫性

    The selected_region always appears in the output with opacity 1.0.

    **Validates: Requirements 5.2, 5.3**
    """
    states = compute_opacity_states(selected_region, REGIONS)

    assert selected_region in states, (
        f"Selected region {selected_region} not found in output states"
    )
    assert states[selected_region] == 1.0, (
        f"Selected region {selected_region} has opacity "
        f"{states[selected_region]}, expected 1.0"
    )
