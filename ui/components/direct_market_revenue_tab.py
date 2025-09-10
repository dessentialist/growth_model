from __future__ import annotations

import streamlit as st

from .base_component import BaseComponent
from ui.services import ValidationService
import pandas as pd


class DirectMarketRevenueTab(BaseComponent):
    """Tab 6: Direct market revenue parameters (Phase 3).

    Product-specific parameters (9) written into `state.direct_market_revenue`
    and mirrored into `state.overrides.constants` using canonical names
    `<param>_<product>` expected by the backend model.
    """

    def __init__(self, state, validation_service: ValidationService) -> None:
        super().__init__(state)
        self.validation_service = validation_service

    def render(self) -> None:
        st.header("Direct Market Revenue Parameters")
        products = list(self.state.simulation_definitions.products)
        if not products:
            st.warning("No products available. Load inputs or set Simulation Definitions.")
            return

        st.caption("Press Enter in a cell to persist the value.")

        tab_ma, tab_od = st.tabs(["Market Activation", "Orders"])
        with tab_ma:
            self._render_market_activation_table(products)
        with tab_od:
            self._render_orders_table(products)

    def _render_market_activation_table(self, products: list[str]) -> None:
        params = [
            "lead_start_year",
            "inbound_lead_generation_rate",
            "outbound_lead_generation_rate",
            "lead_to_c_conversion_rate",
            "TAM",
        ]
        labels = {
            "lead_start_year": "lead_start_year (year)",
            "inbound_lead_generation_rate": "inbound_lead_generation_rate (per quarter)",
            "outbound_lead_generation_rate": "outbound_lead_generation_rate (per quarter)",
            "lead_to_c_conversion_rate": "lead_to_c_conversion_rate (fraction 0-1; e.g., 0.75 = 75%)",
            "TAM": "TAM (count)",
        }
        row_labels = [labels.get(pn, pn) for pn in params]
        col_labels = products

        df_key = "dm_ma_editor"
        reset_count_key = "dm_ma_reset_count"
        if reset_count_key not in st.session_state:
            st.session_state[reset_count_key] = 0
        if df_key not in st.session_state:
            df = pd.DataFrame(index=row_labels, columns=col_labels, dtype=float)
            for prod in products:
                for pn, row in zip(params, row_labels):
                    val = self.state.direct_market_revenue.direct_market_params.get(prod, {}).get(pn, 0.0)
                    df.at[row, prod] = float(val)
            st.session_state[df_key] = df
        else:
            if list(st.session_state[df_key].columns) != col_labels or list(st.session_state[df_key].index) != row_labels:
                df = pd.DataFrame(index=row_labels, columns=col_labels, dtype=float)
                for prod in products:
                    for pn, row in zip(params, row_labels):
                        val = self.state.direct_market_revenue.direct_market_params.get(prod, {}).get(pn, 0.0)
                        df.at[row, prod] = float(val)
                st.session_state[df_key] = df
        use_widget_key = f"dm_ma_editor_widget_{st.session_state[reset_count_key]}"
        if st.button("Reset to default (Market Activation)", key="dm_ma_reset_btn"):
            restored_cells = 0
            for prod in products:
                for pn, row in zip(params, row_labels):
                    const_name = f"{pn}_{prod}"
                    if const_name in self.state.last_saved_constants:
                        st.session_state[df_key].at[row, prod] = float(self.state.last_saved_constants[const_name])
                        restored_cells += 1
            st.session_state[reset_count_key] = int(st.session_state[reset_count_key]) + 1
            use_widget_key = f"dm_ma_editor_widget_{st.session_state[reset_count_key]}"
            st.caption(f"Reset (Direct Market Activation): restored {restored_cells} cells; key={use_widget_key}")

        edited = st.data_editor(
            st.session_state[df_key],
            use_container_width=True,
            num_rows="fixed",
            key=use_widget_key,
        )
        for prod in products:
            for pn, row in zip(params, row_labels):
                try:
                    val = float(edited.at[row, prod])
                except Exception:
                    continue
                self.state.direct_market_revenue.direct_market_params.setdefault(prod, {})[pn] = val
                self.state.overrides.constants[f"{pn}_{prod}"] = val

    def _render_orders_table(self, products: list[str]) -> None:
        params = [
            "lead_to_requirement_delay",
            "requirement_to_fulfilment_delay",
            "avg_order_quantity_initial",
            "client_requirement_growth",
            "requirement_limit_multiplier",
        ]
        labels = {
            "lead_to_requirement_delay": "lead_to_requirement_delay (quarters)",
            "requirement_to_fulfilment_delay": "requirement_to_fulfilment_delay (quarters)",
            "avg_order_quantity_initial": "avg_order_quantity_initial (units)",
            "client_requirement_growth": "client_requirement_growth (fraction per quarter; e.g., 0.05 = 5%)",
            "requirement_limit_multiplier": "requirement_limit_multiplier (× of initial order; e.g., 2.0 = 2×)",
        }
        row_labels = [labels.get(pn, pn) for pn in params]
        col_labels = products

        df_key = "dm_od_editor"
        reset_count_key = "dm_od_reset_count"
        if reset_count_key not in st.session_state:
            st.session_state[reset_count_key] = 0
        if df_key not in st.session_state:
            df = pd.DataFrame(index=row_labels, columns=col_labels, dtype=float)
            for prod in products:
                for pn, row in zip(params, row_labels):
                    val = self.state.direct_market_revenue.direct_market_params.get(prod, {}).get(pn, 0.0)
                    df.at[row, prod] = float(val)
            st.session_state[df_key] = df
        else:
            if list(st.session_state[df_key].columns) != col_labels or list(st.session_state[df_key].index) != row_labels:
                df = pd.DataFrame(index=row_labels, columns=col_labels, dtype=float)
                for prod in products:
                    for pn, row in zip(params, row_labels):
                        val = self.state.direct_market_revenue.direct_market_params.get(prod, {}).get(pn, 0.0)
                        df.at[row, prod] = float(val)
                st.session_state[df_key] = df
        use_widget_key = f"dm_od_editor_widget_{st.session_state[reset_count_key]}"
        if st.button("Reset to default (Orders)", key="dm_od_reset_btn"):
            restored_cells = 0
            for prod in products:
                for pn, row in zip(params, row_labels):
                    const_name = f"{pn}_{prod}"
                    if const_name in self.state.last_saved_constants:
                        st.session_state[df_key].at[row, prod] = float(self.state.last_saved_constants[const_name])
                        restored_cells += 1
            st.session_state[reset_count_key] = int(st.session_state[reset_count_key]) + 1
            use_widget_key = f"dm_od_editor_widget_{st.session_state[reset_count_key]}"
            st.caption(f"Reset (Direct Market Orders): restored {restored_cells} cells; key={use_widget_key}")

        edited = st.data_editor(
            st.session_state[df_key],
            use_container_width=True,
            num_rows="fixed",
            key=use_widget_key,
        )
        for prod in products:
            for pn, row in zip(params, row_labels):
                try:
                    val = float(edited.at[row, prod])
                except Exception:
                    continue
                self.state.direct_market_revenue.direct_market_params.setdefault(prod, {})[pn] = val
                self.state.overrides.constants[f"{pn}_{prod}"] = val


def render_direct_market_revenue_tab(state, validation_service: ValidationService) -> None:
    DirectMarketRevenueTab(state, validation_service).render()


