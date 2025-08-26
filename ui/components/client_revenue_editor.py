"""
Client Revenue Editor Component

This component provides a user interface for managing client revenue parameters
organized in three groups: Market Activation, Orders, and Seeds. It includes
table-based input with save button protection for all 19 parameters.

Author: AI Assistant
Date: 2024
"""

import streamlit as st
import pandas as pd
from typing import List

from ui.state import ClientRevenueState


def render_client_revenue_editor(
    state: ClientRevenueState,
    sector_product_combinations: List[str],
    on_save: callable = None
) -> ClientRevenueState:
    """
    Render the client revenue editor for managing 19 parameters across 3 groups.
    
    Args:
        state: Current client revenue state
        sector_product_combinations: List of sector-product combinations from primary mapping
        on_save: Optional callback function when changes are saved
        
    Returns:
        Updated client revenue state
    """
    
    st.markdown("### Client Revenue Parameters")
    st.caption("Manage comprehensive client revenue parameters organized by sector-product combinations.")
    
    # Initialize state if empty
    if not sector_product_combinations:
        st.warning("⚠️ No sector-product combinations available. Please configure Primary Mapping first.")
        return state
    
    # Initialize parameters if not already set
    _initialize_client_revenue_state(state, sector_product_combinations)
    
    # Create tabs for the three parameter groups
    tab1, tab2, tab3 = st.tabs(["Market Activation", "Orders", "Seeds"])
    
    # Tab 1: Market Activation Parameters (9 parameters)
    with tab1:
        st.markdown("#### Market Activation Parameters")
        st.caption("Parameters controlling market activation and client acquisition.")
        
        market_activation_df = _create_market_activation_dataframe(state, sector_product_combinations)
        updated_market_activation = st.data_editor(
            market_activation_df,
            key="market_activation_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Parameter": st.column_config.TextColumn("Parameter", disabled=True),
                "Description": st.column_config.TextColumn("Description", disabled=True),
                **{sp: st.column_config.NumberColumn(sp, format="%.2f") for sp in sector_product_combinations}
            }
        )
        
        # Update state with changes
        _update_market_activation_state(state, updated_market_activation, sector_product_combinations)
    
    # Tab 2: Orders Parameters (9 parameters)
    with tab2:
        st.markdown("#### Orders Parameters")
        st.caption("Parameters controlling order phases and growth rates.")
        
        orders_df = _create_orders_dataframe(state, sector_product_combinations)
        updated_orders = st.data_editor(
            orders_df,
            key="orders_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Parameter": st.column_config.TextColumn("Parameter", disabled=True),
                "Description": st.column_config.TextColumn("Description", disabled=True),
                **{sp: st.column_config.NumberColumn(sp, format="%.2f") for sp in sector_product_combinations}
            }
        )
        
        # Update state with changes
        _update_orders_state(state, updated_orders, sector_product_combinations)
    
    # Tab 3: Seeds Parameters (3 parameters)
    with tab3:
        st.markdown("#### Seeds Parameters")
        st.caption("Parameters for initial seeding and backlog configuration.")
        
        seeds_df = _create_seeds_dataframe(state, sector_product_combinations)
        updated_seeds = st.data_editor(
            seeds_df,
            key="seeds_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Parameter": st.column_config.TextColumn("Parameter", disabled=True),
                "Description": st.column_config.TextColumn("Description", disabled=True),
                **{sp: st.column_config.NumberColumn(sp, format="%.2f") for sp in sector_product_combinations}
            }
        )
        
        # Update state with changes
        _update_seeds_state(state, updated_seeds, sector_product_combinations)
    
    # Save button and change tracking
    st.markdown("---")
    
    # Check for unsaved changes
    has_changes = _check_for_unsaved_changes(state)
    state.has_unsaved_changes = has_changes
    
    if has_changes:
        st.warning("⚠️ You have unsaved changes. Click Save to persist your changes.")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Save Changes", type="primary", disabled=not has_changes):
            if on_save:
                on_save(state)
            st.success("✅ Client revenue parameters saved successfully!")
            state.has_unsaved_changes = False
            st.rerun()
    
    with col2:
        if has_changes:
            st.caption("Save your changes to prevent data loss.")
        else:
            st.caption("All changes have been saved.")
    
    # Summary section
    render_client_revenue_summary(state, sector_product_combinations)
    
    return state


def _initialize_client_revenue_state(state: ClientRevenueState, sector_product_combinations: List[str]):
    """Initialize the client revenue state with default values if not already set."""
    
    # Market Activation Parameters
    if not state.market_activation_params:
        state.market_activation_params = {}
        for sp in sector_product_combinations:
            state.market_activation_params[sp] = {
                "ATAM": 50.0,
                "anchor_start_year": 2025.0,
                "anchor_lead_generation_rate": 10.0,
                "lead_to_pc_conversion_rate": 0.3,
                "project_generation_rate": 2.0,
                "project_duration": 4.0,
                "projects_to_client_conversion": 0.4,
                "max_projects_per_pc": 3.0,
                "anchor_client_activation_delay": 2.0
            }
    
    # Orders Parameters
    if not state.orders_params:
        state.orders_params = {}
        for sp in sector_product_combinations:
            state.orders_params[sp] = {
                "initial_phase_duration": 2.0,
                "initial_requirement_rate": 100.0,
                "initial_req_growth": 0.2,
                "ramp_phase_duration": 3.0,
                "ramp_requirement_rate": 200.0,
                "ramp_req_growth": 0.15,
                "steady_requirement_rate": 300.0,
                "steady_req_growth": 0.1,
                "requirement_to_order_lag": 1.0
            }
    
    # Seeds Parameters
    if not state.seeds_params:
        state.seeds_params = {}
        for sp in sector_product_combinations:
            state.seeds_params[sp] = {
                "completed_projects_sm": 0.0,
                "active_anchor_clients_sm": 0.0,
                "elapsed_quarters": 0.0
            }


def _create_market_activation_dataframe(state: ClientRevenueState, sector_product_combinations: List[str]) -> pd.DataFrame:
    """Create a DataFrame for market activation parameters."""
    
    # Define parameter descriptions
    param_descriptions = {
        "ATAM": "Total anchor clients for sector-material combination",
        "anchor_start_year": "Year market is activated for sector-material combination",
        "anchor_lead_generation_rate": "Leads per quarter for anchor clients",
        "lead_to_pc_conversion_rate": "Lead to potential client conversion rate",
        "project_generation_rate": "Projects per quarter from potential client",
        "project_duration": "Average project duration in quarters",
        "projects_to_client_conversion": "Projects needed to become client",
        "max_projects_per_pc": "Maximum projects per potential client",
        "anchor_client_activation_delay": "Delay before commercial orders (quarters)"
    }
    
    # Create DataFrame
    data = {"Parameter": [], "Description": []}
    for sp in sector_product_combinations:
        data[sp] = []
    
    for param, description in param_descriptions.items():
        data["Parameter"].append(param)
        data["Description"].append(description)
        for sp in sector_product_combinations:
            value = state.market_activation_params.get(sp, {}).get(param, 0.0)
            data[sp].append(value)
    
    return pd.DataFrame(data)


def _create_orders_dataframe(state: ClientRevenueState, sector_product_combinations: List[str]) -> pd.DataFrame:
    """Create a DataFrame for orders parameters."""
    
    # Define parameter descriptions
    param_descriptions = {
        "initial_phase_duration": "Initial testing phase duration (quarters)",
        "initial_requirement_rate": "Starting kg/quarter/client in initial phase",
        "initial_req_growth": "Percentage growth in initial phase",
        "ramp_phase_duration": "Ramp-up phase duration (quarters)",
        "ramp_requirement_rate": "Starting kg/quarter in ramp phase",
        "ramp_req_growth": "Percentage growth in ramp phase",
        "steady_requirement_rate": "Starting kg/quarter in steady state",
        "steady_req_growth": "Percentage growth in steady state",
        "requirement_to_order_lag": "Requirement to delivery delay (quarters)"
    }
    
    # Create DataFrame
    data = {"Parameter": [], "Description": []}
    for sp in sector_product_combinations:
        data[sp] = []
    
    for param, description in param_descriptions.items():
        data["Parameter"].append(param)
        data["Description"].append(description)
        for sp in sector_product_combinations:
            value = state.orders_params.get(sp, {}).get(param, 0.0)
            data[sp].append(value)
    
    return pd.DataFrame(data)


def _create_seeds_dataframe(state: ClientRevenueState, sector_product_combinations: List[str]) -> pd.DataFrame:
    """Create a DataFrame for seeds parameters."""
    
    # Define parameter descriptions
    param_descriptions = {
        "completed_projects_sm": "Completed projects backlog at T0",
        "active_anchor_clients_sm": "Active clients at T0",
        "elapsed_quarters": "Aging since client activation (quarters)"
    }
    
    # Create DataFrame
    data = {"Parameter": [], "Description": []}
    for sp in sector_product_combinations:
        data[sp] = []
    
    for param, description in param_descriptions.items():
        data["Parameter"].append(param)
        data["Description"].append(description)
        for sp in sector_product_combinations:
            value = state.seeds_params.get(sp, {}).get(param, 0.0)
            data[sp].append(value)
    
    return pd.DataFrame(data)


def _update_market_activation_state(state: ClientRevenueState, df: pd.DataFrame, sector_product_combinations: List[str]):
    """Update the market activation state from the DataFrame."""
    
    for _, row in df.iterrows():
        param = row["Parameter"]
        for sp in sector_product_combinations:
            if sp in df.columns and pd.notna(row[sp]):
                if sp not in state.market_activation_params:
                    state.market_activation_params[sp] = {}
                state.market_activation_params[sp][param] = float(row[sp])


def _update_orders_state(state: ClientRevenueState, df: pd.DataFrame, sector_product_combinations: List[str]):
    """Update the orders state from the DataFrame."""
    
    for _, row in df.iterrows():
        param = row["Parameter"]
        for sp in sector_product_combinations:
            if sp in df.columns and pd.notna(row[sp]):
                if sp not in state.orders_params:
                    state.orders_params[sp] = {}
                state.orders_params[sp][param] = float(row[sp])


def _update_seeds_state(state: ClientRevenueState, df: pd.DataFrame, sector_product_combinations: List[str]):
    """Update the seeds state from the DataFrame."""
    
    for _, row in df.iterrows():
        param = row["Parameter"]
        for sp in sector_product_combinations:
            if sp in df.columns and pd.notna(row[sp]):
                if sp not in state.seeds_params:
                    state.seeds_params[sp] = {}
                state.seeds_params[sp][param] = float(row[sp])


def _check_for_unsaved_changes(state: ClientRevenueState) -> bool:
    """Check if there are any unsaved changes in the state."""
    
    # For now, we'll use the has_unsaved_changes flag
    # In a more sophisticated implementation, we could compare against original values
    return state.has_unsaved_changes


def render_client_revenue_summary(state: ClientRevenueState, sector_product_combinations: List[str]):
    """Render a summary of the current client revenue configuration."""
    
    st.markdown("### Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sector-Product Combinations", len(sector_product_combinations))
        if sector_product_combinations:
            st.caption(", ".join(sector_product_combinations[:3]) + ("..." if len(sector_product_combinations) > 3 else ""))
    
    with col2:
        total_params = len(
            state.market_activation_params.get(
                list(state.market_activation_params.keys())[0] 
                if state.market_activation_params else []
            )
        )
        st.metric("Market Activation Parameters", total_params)
        st.caption("ATAM, anchor_start_year, lead generation, etc.")
    
    with col3:
        total_orders = len(state.orders_params.get(list(state.orders_params.keys())[0] if state.orders_params else []))
        st.metric("Orders Parameters", total_orders)
        st.caption("Phase durations, rates, and growth")
    
    # Show some sample values
    if sector_product_combinations:
        sample_sp = sector_product_combinations[0]
        st.markdown(f"**Sample Values for {sample_sp}:**")
        
        if sample_sp in state.market_activation_params:
            sample_atam = state.market_activation_params[sample_sp].get("ATAM", 0)
            sample_start_year = state.market_activation_params[sample_sp].get("anchor_start_year", 0)
            st.caption(f"ATAM: {sample_atam}, Start Year: {sample_start_year}")
