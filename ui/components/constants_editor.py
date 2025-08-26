from __future__ import annotations

"""
Constants editor component for Streamlit.

Renders a filterable table-like UI to add/edit constant overrides. We only
allow keys from the permissible set to avoid name drift. Values are coerced to
float by Streamlit inputs; backend will re-validate on save.

This component is now framework-agnostic and works with the new state management system.
Phase 2: Enhanced with table-based input using st.data_editor() for improved UX.
"""

from typing import List, Dict
import streamlit as st
import pandas as pd

# Import from the new framework-agnostic business logic
from ui.state import ScenarioOverridesState


def render_constants_editor(
    state: ScenarioOverridesState, 
    permissible_constants: List[str],
    on_constants_update: callable = None
) -> ScenarioOverridesState:
    """Render and return updated constants overrides.

    Args:
        state: Current ScenarioOverridesState containing constants overrides
        permissible_constants: List of permissible constant keys
        on_constants_update: Callback function to update state when constants change

    Returns:
        Updated ScenarioOverridesState with modified constants
    """
    st.subheader("Constants Overrides")
    st.caption("Only permissible keys are listed to ensure correctness.")

    # Get current constants from state
    current_constants = dict(state.constants)

    # Simple search box to filter permissible keys
    query = st.text_input("Filter keys", value="", key="constants_filter").strip().lower()
    filtered = [k for k in permissible_constants if query in k.lower()]
    
    # Guard against empty options to avoid Streamlit errors when filter yields no matches
    key_to_add = None
    if filtered:
        key_to_add = st.selectbox("Select constant name", options=filtered, key="constants_key_select")
    else:
        st.info("No permissible keys match the current filter.")

    # Add new constant
    col1, col2 = st.columns([1, 3])
    with col1:
        val = st.number_input("Value", value=0.0, key="constants_value_input")
    with col2:
        add_btn = st.button("Add/Update", use_container_width=True, key="constants_add_btn")

    if add_btn and key_to_add:
        current_constants[key_to_add] = float(val)
        # Update state if callback provided
        if on_constants_update:
            on_constants_update(current_constants)

    # Existing overrides table with inline editing using st.data_editor()
    if current_constants:
        st.markdown("**Current Constants Overrides:**")
        
        # Convert to DataFrame for st.data_editor()
        constants_data = []
        for k, v in sorted(current_constants.items()):
            constants_data.append({
                "Constant Name": k,
                "Current Value": float(v),
                "Actions": f"actions_{k}"
            })
        
        constants_df = pd.DataFrame(constants_data)
        
        # Use st.data_editor for table-based editing
        edited_df = st.data_editor(
            constants_df,
            column_config={
                "Constant Name": st.column_config.TextColumn(
                    "Constant Name",
                    help="Name of the constant parameter",
                    disabled=True  # Names cannot be edited
                ),
                "Current Value": st.column_config.NumberColumn(
                    "Current Value",
                    help="Numeric value for the constant",
                    min_value=None,
                    max_value=None,
                    step=0.01,
                    format="%.4f"
                ),
                "Actions": st.column_config.Column(
                    "Actions",
                    help="Actions available for this constant"
                )
            },
            hide_index=True,
            key="constants_data_editor"
        )
        
        # Process changes from the data editor
        if not edited_df.equals(constants_df):
            # Update values based on edited data
            for idx, row in edited_df.iterrows():
                constant_name = row["Constant Name"]
                new_value = row["Current Value"]
                if constant_name in current_constants and new_value != current_constants[constant_name]:
                    current_constants[constant_name] = float(new_value)
                    if on_constants_update:
                        on_constants_update(current_constants)
        
        # Add delete buttons below the table for each constant
        st.markdown("**Delete Constants:**")
        delete_cols = st.columns(min(4, len(current_constants)))
        for i, (k, v) in enumerate(sorted(current_constants.items())):
            with delete_cols[i % len(delete_cols)]:
                if st.button(f"🗑️ {k}", key=f"rm_{k}_{i}", type="secondary"):
                    current_constants.pop(k, None)
                    if on_constants_update:
                        on_constants_update(current_constants)
                    st.rerun()
    else:
        st.info("No constants overridden yet.")

    # Summary section
    if current_constants:
        st.markdown("---")
        st.markdown(f"**Total Constants Overridden: {len(current_constants)}**")
        
        # Show all current values in a compact format
        summary_cols = st.columns(3)
        for i, (k, v) in enumerate(sorted(current_constants.items())):
            with summary_cols[i % 3]:
                st.metric(k, f"{v:.4f}")

    # Update the state with the modified constants
    state.constants = current_constants
    return state


def render_constants_summary(constants: Dict[str, float]) -> None:
    """Render a summary view of constants overrides.
    
    Args:
        constants: Dictionary of constant overrides to display
    """
    if not constants:
        st.info("No constants overridden")
        return
    
    st.markdown("**Constants Summary:**")
    
    # Group constants by first letter for better organization
    grouped = {}
    for k in sorted(constants.keys()):
        first_letter = k[0].upper() if k else "Other"
        if first_letter not in grouped:
            grouped[first_letter] = []
        grouped[first_letter].append(k)
    
    # Display grouped constants
    for letter in sorted(grouped.keys()):
        with st.expander(f"{letter} ({len(grouped[letter])})", expanded=False):
            cols = st.columns(2)
            for i, key in enumerate(grouped[letter]):
                with cols[i % 2]:
                    st.metric(key, f"{constants[key]:.4f}")


__all__ = ["render_constants_editor", "render_constants_summary"]
