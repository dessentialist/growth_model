from __future__ import annotations

import streamlit as st

from .base_component import BaseComponent
from ui.state import PrimaryMapEntry
from ui.services import ScenarioService


class PrimaryMappingTab(BaseComponent):
    """Tab 3: Primary Mapping editor (Phase 2).

    Allows selecting a sector, mapping one or more products to it, and assigning
    per-(sector, product) start years. Writes to `state.primary_map.by_sector` in
    the exact schema expected by scenario overrides (Phase 13-compatible).
    """

    def __init__(self, state) -> None:
        super().__init__(state)
        self._scenario_service = ScenarioService()

    def render(self) -> None:
        st.header("Primary Mapping")

        lists = self._scenario_service.get_lists_summary()
        sectors: list[str] = lists.get("sectors", [])
        products: list[str] = lists.get("products", [])

        if not sectors or not products:
            st.error("No sectors/products available from inputs.json. Ensure inputs are loaded correctly.")
            return

        # SM-mode banner and sync notice
        if str(self.state.runspecs.anchor_mode).strip().lower() == "sm":
            st.info("SM mode: lists_sm will be synchronized from this mapping when you save the scenario.")

        # Sector selection
        st.subheader("Select Sector")
        sector = st.selectbox("Sector", options=sectors, index=0)

        # Current mapping entries for selected sector
        current_entries = self.state.primary_map.by_sector.get(sector, [])
        current_products = [e.product for e in current_entries]
        current_start_year_by_product = {e.product: float(e.start_year) for e in current_entries}

        st.subheader("Map Products to Sector")
        selected_products = st.multiselect(
            "Products for this sector",
            options=products,
            default=current_products,
            help="Choose one or more products used by this sector.",
        )

        # Start years editor for selected products
        st.subheader("Start Years by Product")
        cols = st.columns(2)
        left, right = cols[0], cols[1]
        updated_start_years: dict[str, float] = {}
        for idx, p in enumerate(selected_products):
            container = left if (idx % 2 == 0) else right
            with container:
                default_sy = current_start_year_by_product.get(p, 2025.0)
                sy = st.number_input(
                    f"Start Year — {p}",
                    value=float(default_sy),
                    step=1.0,
                    key=f"pm_sy_{sector}_{p}",
                )
                updated_start_years[p] = float(sy)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Apply to Sector", type="primary", use_container_width=True):
                entries = [PrimaryMapEntry(product=p, start_year=updated_start_years.get(p, 2025.0)) for p in selected_products]
                entries.sort(key=lambda x: x.product)
                self.state.primary_map.by_sector[sector] = entries
                st.success(f"Updated mapping for {sector} ({len(entries)} product(s))")
        with col_b:
            if st.button("Clear Sector Mapping", use_container_width=True):
                if sector in self.state.primary_map.by_sector:
                    del self.state.primary_map.by_sector[sector]
                st.warning(f"Cleared mapping for {sector}")
        with col_c:
            if st.button("Clear All Mappings", use_container_width=True):
                self.state.primary_map.by_sector.clear()
                st.warning("Cleared all sector→product mappings")

        st.divider()

        # Mapping insights and summary
        st.subheader("Mapping Insights")
        total_pairs = sum(len(v) for v in self.state.primary_map.by_sector.values())
        st.write(f"Total mapped pairs: :blue[{total_pairs}] across :blue[{len(self.state.primary_map.by_sector)}] sector(s)")

        # If previous lists_sm exists and differs from derived pairs, show diff hint
        if str(self.state.runspecs.anchor_mode).strip().lower() == "sm":
            derived = [(s, e.product) for s, entries in self.state.primary_map.by_sector.items() for e in entries]
            derived.sort(key=lambda x: (x[0], x[1]))
            if self.state.previous_lists_sm and self.state.previous_lists_sm != derived:
                st.warning("lists_sm in the loaded scenario differs from the current mapping. It will be synchronized on save.")

        # Show per-sector summary table
        if self.state.primary_map.by_sector:
            for s, entries in sorted(self.state.primary_map.by_sector.items()):
                with st.expander(f"{s} — {len(entries)} product(s)", expanded=False):
                    for e in entries:
                        warn = " (disabled)" if float(e.start_year) <= 0 else ""
                        st.write(f"• {e.product} — start_year={float(e.start_year)}{warn}")


def render_primary_mapping_tab(state) -> None:
    PrimaryMappingTab(state).render()


