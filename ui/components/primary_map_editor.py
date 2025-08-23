from __future__ import annotations

"""
Primary Map editor component for Streamlit.

This component lets the user propose replacements to the primary sector→materials
mapping with per-(sector, material) start years. It presents a sector selector,
shows current mapping for context, and allows building a proposed list for that
sector with a simple material multi-select and start-year inputs per material.

The state persists in `PrimaryMapState` and is used during Phase 8 validation and
YAML writing as `overrides.primary_map`.
"""

from typing import Dict, List, Tuple
import streamlit as st

from src.phase1_data import Phase1Bundle
from ui.state import PrimaryMapEntry, PrimaryMapState


def _get_current_mapping_for_sector(bundle: Phase1Bundle, sector: str) -> List[Tuple[str, float]]:
    """Return sorted list of (material, start_year) pairs currently mapped for a sector."""
    pm = bundle.primary_map.long
    rows = pm[pm["Sector"].astype(str) == sector]
    entries: List[Tuple[str, float]] = []
    for _, r in rows.iterrows():
        try:
            entries.append((str(r["Material"]), float(r["StartYear"])) )
        except Exception:
            # Fallback to 0.0 if parsing fails; UI will allow editing
            entries.append((str(r["Material"]), 0.0))
    entries.sort(key=lambda x: x[0])
    return entries


def render_primary_map_editor(state: PrimaryMapState, bundle: Phase1Bundle) -> PrimaryMapState:
    """Render the Primary Map editor and return updated `PrimaryMapState`.

    UX flow:
      - Select sector
      - View current mapping (read-only)
      - Choose proposed materials and set start years
      - Apply to state for that sector
    """
    st.subheader("Primary Map Overrides")
    st.caption("Replace a sector's mapped materials with a new set and start years.")

    sectors = list(map(str, bundle.lists.sectors))
    materials = list(map(str, bundle.lists.materials))
    sector = st.selectbox("Select sector", options=sectors)

    # Current mapping preview
    current = _get_current_mapping_for_sector(bundle, sector)
    st.markdown("Current mapping:")
    if current:
        st.table({"Material": [m for m, _ in current], "StartYear": [sy for _, sy in current]})
    else:
        st.info("This sector has no mapped materials in inputs.json.")

    # Proposed mapping editor
    st.markdown("Proposed mapping:")
    # Compute a clear default selection: if we have state for this sector, use it;
    # otherwise default to the current mapping from inputs.json.
    if sector in state.by_sector:
        default_selected = [e.material for e in state.by_sector[sector]]
    else:
        default_selected = [m for m, _ in current]
    selected_materials = st.multiselect(
        "Materials", options=materials, default=default_selected
    )

    # Prepare rows with start years, prefilled from either state or current mapping
    proposed_entries: Dict[str, float] = {}
    # Prefill from state if present
    if sector in state.by_sector:
        for e in state.by_sector[sector]:
            proposed_entries[e.material] = float(e.start_year)
    else:
        for m, sy in current:
            proposed_entries[m] = float(sy)

    # Render start year inputs for each selected material
    updated_entries: List[PrimaryMapEntry] = []
    for m in selected_materials:
        default_sy = proposed_entries.get(m, 2025.0)
        sy = st.number_input(f"StartYear for {m}", value=float(default_sy), step=0.25, format="%.2f", key=f"pm_sy_{sector}_{m}")
        updated_entries.append(PrimaryMapEntry(material=m, start_year=float(sy)))

    # Apply/clear controls
    col_apply, col_clear = st.columns([1, 1])
    with col_apply:
        if st.button("Apply Mapping for Sector", type="primary"):
            # Save only if user selected materials; empty selection clears override for this sector
            if updated_entries:
                state.by_sector[sector] = sorted(updated_entries, key=lambda e: e.material)
            else:
                state.by_sector.pop(sector, None)
    with col_clear:
        if st.button("Clear Override for Sector"):
            state.by_sector.pop(sector, None)

    # Summary
    if state.by_sector:
        st.markdown("Proposed overrides (all sectors):")
        summary_rows = []
        for s, entries in sorted(state.by_sector.items()):
            for e in entries:
                summary_rows.append((s, e.material, e.start_year))
        st.dataframe({"Sector": [r[0] for r in summary_rows], "Material": [r[1] for r in summary_rows], "StartYear": [r[2] for r in summary_rows]}, use_container_width=True)
    else:
        st.info("No primary map overrides proposed yet.")

    return state


__all__ = ["render_primary_map_editor"]



