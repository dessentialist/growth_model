from __future__ import annotations

"""
Time-series (points) editor component for Streamlit.

Allows adding/editing lookup point series (price_*, max_capacity_*) for materials.
We constrain to permissible lookup names and enforce strictly increasing times
with numeric values on the UI side; backend validation will run on save.
"""

from typing import Dict, List, Tuple
import streamlit as st

from ui.state import ScenarioOverridesState


def _render_series_editor(name: str, series: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    st.markdown(f"#### {name}")
    # Provide add/remove controls and display current sorted rows
    rows = list(series)
    col_add1, col_add2, col_add3 = st.columns([2, 2, 1])
    with col_add1:
        t = st.number_input(f"Year for {name}", value=2025.0, step=0.25, key=f"t_{name}")
    with col_add2:
        v = st.number_input(f"Value for {name}", value=0.0, key=f"v_{name}")
    with col_add3:
        if st.button("Add Point", key=f"add_{name}"):
            rows.append((float(t), float(v)))

    # Sort and show rows
    rows.sort(key=lambda x: x[0])
    # Inline increasing-time check
    bad_order = any(rows[i][0] <= rows[i-1][0] for i in range(1, len(rows)))
    if bad_order:
        st.warning("Times must be strictly increasing; adjust or remove duplicates.")

    # Render rows with remove buttons
    to_remove: List[int] = []
    for idx, (tt, vv) in enumerate(rows):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            new_t = st.number_input(f"t[{idx}]", value=float(tt), step=0.25, key=f"row_t_{name}_{idx}")
        with c2:
            new_v = st.number_input(f"v[{idx}]", value=float(vv), key=f"row_v_{name}_{idx}")
        with c3:
            if st.button("Remove", key=f"rm_row_{name}_{idx}"):
                to_remove.append(idx)
        rows[idx] = (float(new_t), float(new_v))
    if to_remove:
        rows = [r for i, r in enumerate(rows) if i not in to_remove]
    return rows


def render_points_editor(overrides: ScenarioOverridesState, permissible_points: List[str]) -> ScenarioOverridesState:
    """Render the points editor and return updated overrides.

    UX:
      - Choose a permissible lookup to edit
      - Manage a list of [time, value] pairs
      - Maintain strictly increasing times
    """
    st.subheader("Time-Series Overrides")
    st.caption("Edit price_*/max_capacity_* lookups. Times must be strictly increasing.")

    query = st.text_input("Filter lookups", value="").strip().lower()
    filtered = [k for k in permissible_points if query in k.lower()]
    # Guard against empty option set
    selected = None
    if filtered:
        selected = st.selectbox("Select lookup name", options=filtered)
    else:
        st.info("No lookups match the current filter.")

    points = dict(overrides.points)
    if selected is not None:
        current_series = points.get(selected, [])
        edited_series = _render_series_editor(selected, current_series)
    else:
        edited_series = []

    # Save button to apply edited series to overrides; keep series only if non-empty
    if st.button("Apply Series"):
        if selected is not None:
            if edited_series:
                points[selected] = edited_series
            else:
                points.pop(selected, None)

    # Quick summary of current overrides
    if points:
        st.markdown("Current series overridden:")
        st.write(sorted(points.keys()))
    else:
        st.info("No lookup series overridden yet.")

    overrides.points = points
    return overrides


__all__ = ["render_points_editor"]


