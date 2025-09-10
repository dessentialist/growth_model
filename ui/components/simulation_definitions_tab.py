from __future__ import annotations

import streamlit as st

from .base_component import BaseComponent
from ui.utils.helpers import ensure_unique_sorted


class SimulationDefinitionsTab(BaseComponent):
    """Tab 1: Market/Sector/Product lists (Phase 1).

    Provides simple list editors with add/remove controls; persistence is
    handled via the Specs tab's Save for Phase 1.
    """

    def render(self) -> None:
        st.header("Simulation Definitions")
        st.caption("Manage Markets, Sectors, and Products.")

        self._render_list_editor(
            title="Markets",
            items=self.state.simulation_definitions.markets,
            on_update=lambda updated: self._set_list("markets", updated),
        )
        self._render_list_editor(
            title="Sectors",
            items=self.state.simulation_definitions.sectors,
            on_update=lambda updated: self._set_list("sectors", updated),
        )
        self._render_list_editor(
            title="Products",
            items=self.state.simulation_definitions.products,
            on_update=lambda updated: self._set_list("products", updated),
        )

    def _set_list(self, field_name: str, values: list[str]) -> None:
        setattr(self.state.simulation_definitions, field_name, ensure_unique_sorted(values))
        # Track unsaved changes so the user is aware to save via Specs tab
        self.state.simulation_definitions.has_unsaved_changes = True

    def _render_list_editor(self, title: str, items: list[str], on_update) -> None:
        st.subheader(title)
        st.write(
            "Add or remove entries. Duplicates are removed and the list is kept sorted for consistency."
        )
        if self.state.simulation_definitions.has_unsaved_changes:
            st.warning("You have unsaved changes. Use the Specs tab to Save.")
        # Show current list
        st.write(items)
        col1, col2 = st.columns(2)
        with col1:
            new_item = st.text_input(f"Add {title[:-1] if title.endswith('s') else title}", key=f"add_{title}")
            if st.button(f"Add to {title}") and new_item.strip():
                updated = items + [new_item.strip()]
                on_update(updated)
                st.success(f"Added '{new_item.strip()}'")
        with col2:
            if items:
                remove_item = st.selectbox(f"Remove from {title}", options=[""] + items, index=0, key=f"rm_{title}")
                if st.button(f"Remove from {title}") and remove_item:
                    updated = [i for i in items if i != remove_item]
                    on_update(updated)
                    st.warning(f"Removed '{remove_item}'")


def render_simulation_definitions_tab(state) -> None:
    SimulationDefinitionsTab(state).render()


