from __future__ import annotations

import streamlit as st

from .base_component import BaseComponent
from ui.services import ScenarioService, ValidationService
import pandas as pd


class LookupPointsTab(BaseComponent):
    """Tab 7: Lookup points for capacity and pricing (Phase 3).

    Provides simple editors for `max_capacity_<product>` and `price_<product>`
    lookups as tables of [year, value] pairs. Writes to `state.overrides.points`.
    """

    def __init__(self, state, scenario_service: ScenarioService, validation_service: ValidationService) -> None:
        super().__init__(state)
        self.scenario_service = scenario_service
        self.validation_service = validation_service

    def render(self) -> None:
        st.header("Lookup Points")
        lists = self.scenario_service.get_lists_summary()
        products: list[str] = lists.get("products", [])
        if not products:
            st.warning("No products available. Load inputs or set Simulation Definitions.")
            return

        st.caption("Edit yearly points; the model handles per-quarter scaling and hold-last policy.")

        self._render_production_capacity(products)
        st.divider()
        self._render_pricing(products)


    def _render_production_capacity(self, products: list[str]) -> None:
        st.subheader("Production Capacity (max_capacity_<product>)")
        # Build a table with years as rows and products as columns
        # Use union of all years present in last_saved_points or current overrides
        all_years = set()
        for p in products:
            name = f"max_capacity_{p}"
            for (t, _) in self.state.overrides.points.get(name, []) or []:
                all_years.add(float(t))
            for (t, _) in self.state.last_saved_points.get(name, []) or []:
                all_years.add(float(t))
        if not all_years:
            all_years = {float(self.state.runspecs.starttime)}
        years = sorted(list(all_years))

        df_key = "lp_capacity_editor"
        reset_count_key = "lp_cap_reset_count"
        if reset_count_key not in st.session_state:
            st.session_state[reset_count_key] = 0
        if df_key not in st.session_state:
            df = pd.DataFrame(index=[int(y) for y in years], columns=products, dtype=float)
            for p in products:
                name = f"max_capacity_{p}"
                vals = {int(t): float(v) for (t, v) in self.state.overrides.points.get(name, [])}
                for y in years:
                    df.at[int(y), p] = float(vals.get(int(y), 0.0))
            st.session_state[df_key] = df
        else:
            if list(st.session_state[df_key].columns) != products:
                df = pd.DataFrame(index=st.session_state[df_key].index, columns=products, dtype=float)
                st.session_state[df_key] = df

        col1, col2 = st.columns(2)
        with col1:
            add_year = st.number_input("Add year", value=int(self.state.runspecs.starttime), step=1, key="lp_cap_add_year")
            if st.button("Add row", key="lp_cap_add_row"):
                if int(add_year) not in st.session_state[df_key].index:
                    st.session_state[df_key].loc[int(add_year)] = [0.0] * len(products)
                    st.session_state[df_key] = st.session_state[df_key].sort_index()
        with col2:
            if st.button("Reset to default (Capacity)", key="lp_cap_reset_btn"):
                restored_cells = 0
                for p in products:
                    name = f"max_capacity_{p}"
                    vals = {int(t): float(v) for (t, v) in self.state.last_saved_points.get(name, [])}
                    for y in st.session_state[df_key].index:
                        if int(y) in vals:
                            st.session_state[df_key].at[y, p] = float(vals[int(y)])
                            restored_cells += 1
                st.session_state[reset_count_key] = int(st.session_state[reset_count_key]) + 1
                st.caption(f"Reset (Capacity): restored {restored_cells} cells")

        use_widget_key = f"lp_cap_editor_widget_{st.session_state[reset_count_key]}"
        edited = st.data_editor(st.session_state[df_key], use_container_width=True, num_rows="dynamic", key=use_widget_key)
        # Persist edited table back to overrides.points per product
        for p in products:
            name = f"max_capacity_{p}"
            series = []
            for y in edited.index:
                try:
                    v = float(edited.at[y, p])
                except Exception:
                    continue
                # Only store non-negative values; zero is allowed
                series.append((float(y), float(v)))
            series.sort(key=lambda x: x[0])
            self.state.overrides.points[name] = series

    def _render_pricing(self, products: list[str]) -> None:
        st.subheader("Pricing (price_<product>)")
        all_years = set()
        for p in products:
            name = f"price_{p}"
            for (t, _) in self.state.overrides.points.get(name, []) or []:
                all_years.add(float(t))
            for (t, _) in self.state.last_saved_points.get(name, []) or []:
                all_years.add(float(t))
        if not all_years:
            all_years = {float(self.state.runspecs.starttime)}
        years = sorted(list(all_years))

        df_key = "lp_price_editor"
        reset_count_key = "lp_price_reset_count"
        if reset_count_key not in st.session_state:
            st.session_state[reset_count_key] = 0
        if df_key not in st.session_state:
            df = pd.DataFrame(index=[int(y) for y in years], columns=products, dtype=float)
            for p in products:
                name = f"price_{p}"
                vals = {int(t): float(v) for (t, v) in self.state.overrides.points.get(name, [])}
                for y in years:
                    df.at[int(y), p] = float(vals.get(int(y), 0.0))
            st.session_state[df_key] = df
        else:
            if list(st.session_state[df_key].columns) != products:
                df = pd.DataFrame(index=st.session_state[df_key].index, columns=products, dtype=float)
                st.session_state[df_key] = df

        col1, col2 = st.columns(2)
        with col1:
            add_year = st.number_input("Add year (price)", value=int(self.state.runspecs.starttime), step=1, key="lp_price_add_year")
            if st.button("Add row (price)", key="lp_price_add_row"):
                if int(add_year) not in st.session_state[df_key].index:
                    st.session_state[df_key].loc[int(add_year)] = [0.0] * len(products)
                    st.session_state[df_key] = st.session_state[df_key].sort_index()
        with col2:
            if st.button("Reset to default (Pricing)", key="lp_price_reset_btn"):
                restored_cells = 0
                for p in products:
                    name = f"price_{p}"
                    vals = {int(t): float(v) for (t, v) in self.state.last_saved_points.get(name, [])}
                    for y in st.session_state[df_key].index:
                        if int(y) in vals:
                            st.session_state[df_key].at[y, p] = float(vals[int(y)])
                            restored_cells += 1
                st.session_state[reset_count_key] = int(st.session_state[reset_count_key]) + 1
                st.caption(f"Reset (Pricing): restored {restored_cells} cells")

        use_widget_key = f"lp_price_editor_widget_{st.session_state[reset_count_key]}"
        edited = st.data_editor(st.session_state[df_key], use_container_width=True, num_rows="dynamic", key=use_widget_key)
        for p in products:
            name = f"price_{p}"
            series = []
            for y in edited.index:
                try:
                    v = float(edited.at[y, p])
                except Exception:
                    continue
                series.append((float(y), float(v)))
            series.sort(key=lambda x: x[0])
            self.state.overrides.points[name] = series


def render_lookup_points_tab(state, scenario_service: ScenarioService, validation_service: ValidationService) -> None:
    LookupPointsTab(state, scenario_service, validation_service).render()


