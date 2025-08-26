from __future__ import annotations

"""
Enhanced Primary Map editor component for Streamlit.

This component lets the user propose replacements to the primary sector→products
mapping with per-(sector, product) start years. It presents a sector selector,
shows current mapping for context, and allows building a proposed list for that
sector with a simple product multi-select and start-year inputs per product.

The state persists in `PrimaryMapState` and is used during Phase 8 validation and
YAML writing as `overrides.primary_map`.

Enhanced with save protection, change tracking, and dynamic table generation.
"""

from typing import Dict, List, Tuple, Optional
import streamlit as st
import pandas as pd

from src.phase1_data import Phase1Bundle
from ui.state import PrimaryMapEntry, PrimaryMapState


def _get_current_mapping_for_sector(bundle: Phase1Bundle, sector: str) -> List[Tuple[str, float]]:
    """Return sorted list of (product, start_year) pairs currently mapped for a sector."""
    pm = bundle.primary_map.long
    rows = pm[pm["Sector"].astype(str) == sector]
    entries: List[Tuple[str, float]] = []
    for _, r in rows.iterrows():
        try:
            entries.append((str(r["Material"]), float(r["StartYear"])))
        except Exception:
            # Fallback to 0.0 if parsing fails; UI will allow editing
            entries.append((str(r["Material"]), 0.0))
    entries.sort(key=lambda x: x[0])
    return entries


def _generate_mapping_insights(
    bundle: Phase1Bundle, 
    sector: str, 
    proposed_entries: List[PrimaryMapEntry]
) -> Dict[str, any]:
    """Generate insights and summary for the current sector mapping."""
    current = _get_current_mapping_for_sector(bundle, sector)
    
    insights = {
        "current_count": len(current),
        "proposed_count": len(proposed_entries),
        "changes_made": len(current) != len(proposed_entries),
        "products_added": [],
        "products_removed": [],
        "start_year_changes": []
    }
    
    # Find added/removed products
    current_products = {p for p, _ in current}
    proposed_products = {e.product for e in proposed_entries}
    
    insights["products_added"] = list(proposed_products - current_products)
    insights["products_removed"] = list(current_products - proposed_products)
    
    # Find start year changes
    current_dict = {p: sy for p, sy in current}
    for entry in proposed_entries:
        if entry.product in current_dict:
            old_year = current_dict[entry.product]
            if abs(entry.start_year - old_year) > 0.01:  # Allow small floating point differences
                insights["start_year_changes"].append({
                    "product": entry.product,
                    "old_year": old_year,
                    "new_year": entry.start_year,
                    "change": entry.start_year - old_year
                })
    
    return insights


def render_primary_map_editor(
    state: PrimaryMapState, 
    bundle: Phase1Bundle,
    on_save_callback: Optional[callable] = None
) -> PrimaryMapState:
    """Render the enhanced Primary Map editor and return updated `PrimaryMapState`.

    UX flow:
      - Select sector
      - View current mapping (read-only)
      - Choose proposed products and set start years
      - Apply to state for that sector
      - Save changes with protection
      
    Enhanced with:
      - Save protection and change tracking
      - Dynamic table generation
      - Mapping insights and summary
      - Better visual organization
    """
    st.subheader("Primary Map Overrides")
    st.caption("Replace a sector's mapped products with a new set and start years.")
    
    # Create a copy of the current state for editing
    editing_state = PrimaryMapState()
    editing_state.by_sector = dict(state.by_sector)
    
    # Track if changes were made
    changes_made = False
    
    sectors = list(map(str, bundle.lists.sectors))
    products_list = list(map(str, bundle.lists.products))
    
    # Sector Selection Section
    st.markdown("**Sector Selection**")
    sector = st.selectbox(
        "Select sector to edit", 
        options=sectors,
        help="Choose which sector's product mapping to modify"
    )
    
    # Current Mapping Preview Section
    st.markdown("**Current Mapping**")
    current = _get_current_mapping_for_sector(bundle, sector)
    
    if current:
        current_df = pd.DataFrame({
            "Product": [m for m, _ in current],
            "Start Year": [f"{sy:.2f}" for _, sy in current]
        })
        st.dataframe(current_df, use_container_width=True)
    else:
        st.info("This sector has no mapped products in inputs.json.")
    
    # Proposed Mapping Editor Section
    st.markdown("**Proposed Mapping**")
    
    # Compute a clear default selection: if we have state for this sector, use it;
    # otherwise default to the current mapping from inputs.json.
    if sector in editing_state.by_sector:
        default_selected = [e.product for e in editing_state.by_sector[sector]]
    else:
        default_selected = [m for m, _ in current]
    
    selected_products = st.multiselect(
        "Select products for this sector", 
        options=products_list, 
        default=default_selected,
        help="Choose which products should be mapped to this sector"
    )
    
    # Prepare rows with start years, prefilled from either state or current mapping
    proposed_entries: Dict[str, float] = {}
    
    # Prefill from state if present
    if sector in editing_state.by_sector:
        for e in editing_state.by_sector[sector]:
            proposed_entries[e.product] = float(e.start_year)
    else:
        for m, sy in current:
            proposed_entries[m] = float(sy)
    
    # Render start year inputs for each selected product
    updated_entries: List[PrimaryMapEntry] = []
    
    if selected_products:
        st.markdown("**Set Start Years**")
        st.caption("Configure when each product becomes available in this sector.")
        
        # Create a table-like interface for start years
        year_cols = st.columns(min(len(selected_products), 4))
        
        for i, product in enumerate(selected_products):
            col_idx = i % len(year_cols)
            with year_cols[col_idx]:
                default_sy = proposed_entries.get(product, 2025.0)
                new_year = st.number_input(
                    f"Start Year for {product}",
                    value=float(default_sy),
                    step=0.25,
                    format="%.2f",
                    key=f"pm_sy_{sector}_{product}",
                    help=f"Year when {product} becomes available in {sector}"
                )
                
                # Check if this value changed
                if abs(new_year - default_sy) > 0.01:
                    changes_made = True
                
                updated_entries.append(PrimaryMapEntry(product=product, start_year=float(new_year)))
        
        # Sort entries by product name for consistency
        updated_entries.sort(key=lambda e: e.product)
    
    # Apply/Clear Controls Section
    st.markdown("**Apply Changes**")
    
    col_apply, col_clear = st.columns([1, 1])
    with col_apply:
        if st.button("Apply Mapping for Sector", type="primary"):
            # Save only if user selected products; empty selection clears override for this sector
            if updated_entries:
                editing_state.by_sector[sector] = sorted(updated_entries, key=lambda e: e.product)
            else:
                editing_state.by_sector.pop(sector, None)
            
            changes_made = True
            st.success("✅ Mapping applied for this sector!")
    
    with col_clear:
        if st.button("Clear Override for Sector"):
            editing_state.by_sector.pop(sector, None)
            changes_made = True
            st.success("✅ Override cleared for this sector!")
    
    # Mapping Insights Section
    if updated_entries:
        st.markdown("**Mapping Insights**")
        insights = _generate_mapping_insights(bundle, sector, updated_entries)
        
        # Display insights in an organized way
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Products", insights["current_count"])
        
        with col2:
            st.metric("Proposed Products", insights["proposed_count"])
        
        with col3:
            change_indicator = "🔄" if insights["changes_made"] else "✅"
            st.metric("Status", f"{change_indicator} {'Modified' if insights['changes_made'] else 'No Changes'}")
        
        # Show detailed changes
        if insights["products_added"]:
            st.success(f"➕ **Products Added**: {', '.join(insights['products_added'])}")
        
        if insights["products_removed"]:
            st.warning(f"➖ **Products Removed**: {', '.join(insights['products_removed'])}")
        
        if insights["start_year_changes"]:
            st.info("🕒 **Start Year Changes**:")
            for change in insights["start_year_changes"]:
                direction = "→" if change["change"] > 0 else "←"
                st.caption(f"  {change['product']}: {change['old_year']:.2f} {direction} {change['new_year']:.2f}")
    
    # Save Button Section
    st.markdown("**Save All Changes**")
    
    # Show unsaved changes indicator
    if changes_made:
        st.warning("⚠️ You have unsaved changes. Click Save to apply them to the scenario.")
    
    # Save button with change protection
    col1, col2 = st.columns([1, 3])
    with col1:
        save_clicked = st.button(
            "💾 Save All Changes", 
            type="primary",
            disabled=not changes_made,
            help="Save all mapping changes to the current scenario"
        )
    
    with col2:
        if changes_made:
            st.caption("All mapping changes will be saved to the current scenario configuration.")
        else:
            st.caption("No changes to save.")
    
    # Handle save action
    if save_clicked and changes_made:
        try:
            # Update the original state
            state.by_sector = dict(editing_state.by_sector)
            
            # Call save callback if provided
            if on_save_callback:
                on_save_callback(state)
            
            st.success("✅ All mapping changes saved successfully!")
            changes_made = False
            
        except Exception as e:
            st.error(f"❌ Error saving mapping changes: {e}")
    
    # Summary Section
    st.markdown("**Current Overrides Summary**")
    
    if editing_state.by_sector:
        summary_rows = []
        for s, entries in sorted(editing_state.by_sector.items()):
            for e in entries:
                summary_rows.append((s, e.product, e.start_year))
        
        summary_df = pd.DataFrame({
            "Sector": [r[0] for r in summary_rows],
            "Product": [r[1] for r in summary_rows],
            "Start Year": [f"{r[2]:.2f}" for r in summary_rows],
        })
        
        st.dataframe(summary_df, use_container_width=True)
        
        # Show statistics
        total_sectors = len(editing_state.by_sector)
        total_products = len(summary_rows)
        st.caption(f"📊 **Summary**: {total_sectors} sectors with {total_products} total product mappings")
        
    else:
        st.info("No primary map overrides proposed yet.")
    
    return editing_state


__all__ = ["render_primary_map_editor"]
