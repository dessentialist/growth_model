from __future__ import annotations

import streamlit as st

from .base_component import BaseComponent
from ui.services import ValidationService
import pandas as pd


class ClientRevenueTab(BaseComponent):
    """Tab 5: Client revenue parameters (Phase 3).

    Edits per-(sector, product) parameters grouped as:
    - Market Activation (sector-level behavior applied per pair)
    - Orders (phase rates, growths, lags, and overrides)

    The grid of sector–product pairs is derived from Primary Mapping.
    Writes values into `state.client_revenue.*` and mirrors into
    `state.overrides.constants` using canonical names.
    """

    def __init__(self, state, validation_service: ValidationService) -> None:
        super().__init__(state)
        self.validation_service = validation_service

    def render(self) -> None:
        st.header("Client Revenue Parameters")
        pairs = []
        for sector, entries in self.state.primary_map.by_sector.items():
            for e in entries:
                pairs.append((sector, e.product))
        pairs.sort(key=lambda x: (x[0], x[1]))
        if not pairs:
            st.warning("Configure Primary Mapping first to edit per-(sector, product) parameters.")
            return

        st.caption("Press Enter in a cell to persist the value.")

        tab_ma, tab_od = st.tabs(["Market Activation", "Orders"])
        with tab_ma:
            self._render_market_activation_table(pairs)
        with tab_od:
            self._render_orders_table(pairs)

    def _render_market_activation_table(self, pairs: list[tuple[str, str]]) -> None:
        params = [
            "anchor_start_year",
            "anchor_client_activation_delay",
            "anchor_lead_generation_rate",
            "lead_to_pc_conversion_rate",
            "project_generation_rate",
            "max_projects_per_pc",
            "project_duration",
            "projects_to_client_conversion",
            "ATAM",
        ]
        labels = {
            "anchor_start_year": "anchor_start_year (year)",
            "anchor_client_activation_delay": "anchor_client_activation_delay (quarters)",
            "anchor_lead_generation_rate": "anchor_lead_generation_rate (per quarter)",
            "lead_to_pc_conversion_rate": "lead_to_pc_conversion_rate (fraction 0-1; e.g., 0.75 = 75%)",
            "project_generation_rate": "project_generation_rate (per quarter per PC)",
            "max_projects_per_pc": "max_projects_per_pc (count)",
            "project_duration": "project_duration (quarters)",
            "projects_to_client_conversion": "projects_to_client_conversion (count)",
            "ATAM": "ATAM (count)",
        }
        col_labels = [f"{s} / {p}" for (s, p) in pairs]
        row_labels = [labels.get(p, p) for p in params]

        # Build initial DataFrame from state
        df_key = "cr_ma_editor"
        # Initialize per-subtab reset counter used to rotate editor widget keys
        reset_count_key = "cr_ma_reset_count"
        if reset_count_key not in st.session_state:
            st.session_state[reset_count_key] = 0
        if df_key not in st.session_state:
            df = pd.DataFrame(index=row_labels, columns=col_labels, dtype=float)
            for (s, p) in pairs:
                sp = f"{s}_{p}"
                for param, row in zip(params, row_labels):
                    val = self.state.client_revenue.market_activation_params.get(sp, {}).get(param, 0.0)
                    df.at[row, f"{s} / {p}"] = float(val)
            st.session_state[df_key] = df
        else:
            # If columns/pairs changed, rebuild
            if list(st.session_state[df_key].columns) != col_labels or list(st.session_state[df_key].index) != row_labels:
                df = pd.DataFrame(index=row_labels, columns=col_labels, dtype=float)
                for (s, p) in pairs:
                    sp = f"{s}_{p}"
                    for param, row in zip(params, row_labels):
                        val = self.state.client_revenue.market_activation_params.get(sp, {}).get(param, 0.0)
                        df.at[row, f"{s} / {p}"] = float(val)
                st.session_state[df_key] = df

        # Reset button: rebuild from last-saved YAML and rotate widget key so editor discards prior state
        use_widget_key = f"cr_ma_editor_widget_{st.session_state[reset_count_key]}"
        if st.button("Reset to default (Market Activation)", key="cr_ma_reset_btn"):
            restored_cells = 0
            for (s, p) in pairs:
                for param, row in zip(params, row_labels):
                    const_name = f"{param}_{s}_{p}"
                    if const_name in self.state.last_saved_constants:
                        st.session_state[df_key].at[row, f"{s} / {p}"] = float(self.state.last_saved_constants[const_name])
                        restored_cells += 1
            st.session_state[reset_count_key] = int(st.session_state[reset_count_key]) + 1
            use_widget_key = f"cr_ma_editor_widget_{st.session_state[reset_count_key]}"
            st.caption(f"Reset (Market Activation): restored {restored_cells} cells; key={use_widget_key}")

        edited = st.data_editor(
            st.session_state[df_key],
            use_container_width=True,
            num_rows="fixed",
            key=use_widget_key,
        )
        # Persist edits back to state and mirror to overrides
        for (s, p) in pairs:
            sp = f"{s}_{p}"
            for param, row in zip(params, row_labels):
                try:
                    val = float(edited.at[row, f"{s} / {p}"])
                except Exception:
                    continue
                self.state.client_revenue.market_activation_params.setdefault(sp, {})[param] = val
                self.state.overrides.constants[f"{param}_{s}_{p}"] = val

    def _render_orders_table(self, pairs: list[tuple[str, str]]) -> None:
        params = [
            "initial_phase_duration",
            "initial_requirement_rate",
            "initial_req_growth",
            "ramp_phase_duration",
            "ramp_requirement_rate",
            "ramp_req_growth",
            "steady_requirement_rate",
            "steady_req_growth",
            "requirement_to_order_lag",
            "ramp_requirement_rate_override",
            "steady_requirement_rate_override",
            "requirement_limit_multiplier",
        ]
        labels = {
            "initial_phase_duration": "initial_phase_duration (quarters)",
            "initial_requirement_rate": "initial_requirement_rate (units per quarter)",
            "initial_req_growth": "initial_req_growth (fraction per quarter; e.g., 0.05 = 5%)",
            "ramp_phase_duration": "ramp_phase_duration (quarters)",
            "ramp_requirement_rate": "ramp_requirement_rate (units per quarter; 0 = inherit)",
            "ramp_req_growth": "ramp_req_growth (fraction per quarter; e.g., 0.05 = 5%)",
            "steady_requirement_rate": "steady_requirement_rate (units per quarter; 0 = inherit)",
            "steady_req_growth": "steady_req_growth (fraction per quarter; e.g., 0.05 = 5%)",
            "requirement_to_order_lag": "requirement_to_order_lag (quarters)",
            "ramp_requirement_rate_override": "ramp_requirement_rate_override (units per quarter; optional)",
            "steady_requirement_rate_override": "steady_requirement_rate_override (units per quarter; optional)",
            "requirement_limit_multiplier": "requirement_limit_multiplier (× of initial rate; e.g., 2.0 = 2×)",
        }
        col_labels = [f"{s} / {p}" for (s, p) in pairs]
        row_labels = [labels.get(p, p) for p in params]

        df_key = "cr_od_editor"
        reset_count_key = "cr_od_reset_count"
        if reset_count_key not in st.session_state:
            st.session_state[reset_count_key] = 0
        if df_key not in st.session_state:
            df = pd.DataFrame(index=row_labels, columns=col_labels, dtype=float)
            for (s, p) in pairs:
                sp = f"{s}_{p}"
                for param, row in zip(params, row_labels):
                    val = self.state.client_revenue.orders_params.get(sp, {}).get(param, 0.0)
                    df.at[row, f"{s} / {p}"] = float(val)
            st.session_state[df_key] = df
        else:
            if list(st.session_state[df_key].columns) != col_labels or list(st.session_state[df_key].index) != row_labels:
                df = pd.DataFrame(index=row_labels, columns=col_labels, dtype=float)
                for (s, p) in pairs:
                    sp = f"{s}_{p}"
                    for param, row in zip(params, row_labels):
                        val = self.state.client_revenue.orders_params.get(sp, {}).get(param, 0.0)
                        df.at[row, f"{s} / {p}"] = float(val)
                st.session_state[df_key] = df
        use_widget_key = f"cr_od_editor_widget_{st.session_state[reset_count_key]}"
        if st.button("Reset to default (Orders)", key="cr_od_reset_btn"):
            restored_cells = 0
            for (s, p) in pairs:
                for param, row in zip(params, row_labels):
                    const_name = f"{param}_{s}_{p}"
                    if const_name in self.state.last_saved_constants:
                        st.session_state[df_key].at[row, f"{s} / {p}"] = float(self.state.last_saved_constants[const_name])
                        restored_cells += 1
            st.session_state[reset_count_key] = int(st.session_state[reset_count_key]) + 1
            use_widget_key = f"cr_od_editor_widget_{st.session_state[reset_count_key]}"
            st.caption(f"Reset (Orders): restored {restored_cells} cells; key={use_widget_key}")

        edited = st.data_editor(
            st.session_state[df_key],
            use_container_width=True,
            num_rows="fixed",
            key=use_widget_key,
        )
        for (s, p) in pairs:
            sp = f"{s}_{p}"
            for param, row in zip(params, row_labels):
                try:
                    val = float(edited.at[row, f"{s} / {p}"])
                except Exception:
                    continue
                self.state.client_revenue.orders_params.setdefault(sp, {})[param] = val
                self.state.overrides.constants[f"{param}_{s}_{p}"] = val


def render_client_revenue_tab(state, validation_service: ValidationService) -> None:
    ClientRevenueTab(state, validation_service).render()


