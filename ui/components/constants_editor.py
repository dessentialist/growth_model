from __future__ import annotations

"""
Constants editor component for Streamlit.

Renders a filterable table-like UI to add/edit constant overrides. We only
allow keys from the permissible set to avoid name drift. Values are coerced to
float by Streamlit inputs; backend will re-validate on save.
"""

from typing import Dict, List, Tuple
import streamlit as st

from ui.state import ScenarioOverridesState


def render_constants_editor(overrides: ScenarioOverridesState, permissible_constants: List[str]) -> ScenarioOverridesState:
    """Render and return updated overrides with constants edited.

    UX:
      - Search/select a permissible key
      - Enter a numeric value
      - Add to the current overrides map
      - Show current overrides with remove buttons
    """
    st.subheader("Constants Overrides")
    st.caption("Only permissible keys are listed to ensure correctness.")

    # Simple search box to filter permissible keys
    query = st.text_input("Filter keys", value="").strip().lower()
    filtered = [k for k in permissible_constants if query in k.lower()]
    # Guard against empty options to avoid Streamlit errors when filter yields no matches
    key_to_add = None
    if filtered:
        key_to_add = st.selectbox("Select constant name", options=filtered)
    else:
        st.info("No permissible keys match the current filter.")
    col1, col2 = st.columns([1, 3])
    with col1:
        val = st.number_input("Value", value=0.0)
    with col2:
        add_btn = st.button("Add/Update", use_container_width=True)

    constants = dict(overrides.constants)
    if add_btn and key_to_add:
        constants[key_to_add] = float(val)

    # Existing overrides table
    if constants:
        st.markdown("Current overrides:")
        # Display as key/value pairs with remove buttons
        for k in sorted(constants.keys()):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.text(k)
            with c2:
                new_val = st.number_input(f"{k}", value=float(constants[k]), key=f"const_{k}")
            with c3:
                if st.button("Remove", key=f"rm_{k}"):
                    constants.pop(k, None)
                else:
                    constants[k] = float(new_val)
    else:
        st.info("No constants overridden yet.")

    overrides.constants = constants
    return overrides


__all__ = ["render_constants_editor"]


