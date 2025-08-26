"""
Direct Market Revenue Editor Component

This component provides a user interface for managing direct market revenue parameters
for each product. It includes table-based input with save button protection for all 9 parameters.

Author: AI Assistant
Date: 2024
"""

import streamlit as st
import pandas as pd
from typing import List

from ui.state import DirectMarketRevenueState


def render_direct_market_revenue_editor(
    state: DirectMarketRevenueState,
    sector_product_combinations: List[str],
    on_save: callable = None
) -> DirectMarketRevenueState:
    """
    Render the direct market revenue editor for managing 9 parameters per product.
    
    Args:
        state: Current direct market revenue state
        sector_product_combinations: List of sector-product combinations from primary mapping
        on_save: Optional callback function when changes are saved
        
    Returns:
        Updated direct market revenue state
    """
    
    st.markdown("### Direct Market Revenue Parameters")
    st.caption("Manage product-specific direct market revenue parameters for each sector-product combination.")
    
    # Initialize state if empty
    if not sector_product_combinations:
        st.warning("⚠️ No sector-product combinations available. Please configure Primary Mapping first.")
        return state
    
    # Initialize parameters if not already set
    _initialize_direct_market_revenue_state(state, sector_product_combinations)
    
    # Create the main parameter table
    st.markdown("#### Direct Market Revenue Parameters")
    st.caption("Parameters controlling direct market revenue generation and client acquisition.")
    
    # Create DataFrame for all parameters
    direct_market_df = _create_direct_market_revenue_dataframe(
        state, 
        sector_product_combinations
    )
    
    # Render the data editor
    updated_direct_market = st.data_editor(
        direct_market_df,
        key="direct_market_revenue_editor",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Parameter": st.column_config.TextColumn("Parameter", disabled=True),
            "Description": st.column_config.TextColumn("Description", disabled=True),
            **{sp: st.column_config.NumberColumn(sp, format="%.2f") for sp in sector_product_combinations}
        }
    )
    
    # Update state with changes
    _update_direct_market_revenue_state(state, updated_direct_market, sector_product_combinations)
    
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
            st.success("✅ Direct market revenue parameters saved successfully!")
            state.has_unsaved_changes = False
            st.rerun()
    
    with col2:
        if has_changes:
            st.caption("Save your changes to prevent data loss.")
        else:
            st.caption("All changes have been saved.")
    
    # Summary section
    render_direct_market_revenue_summary(state, sector_product_combinations)
    
    return state


def _initialize_direct_market_revenue_state(state: DirectMarketRevenueState, sector_product_combinations: List[str]):
    """Initialize the direct market revenue state with default values if not already set."""
    
    if not state.direct_market_params:
        state.direct_market_params = {}
        for sp in sector_product_combinations:
            state.direct_market_params[sp] = {
                "lead_start_year": 2025.0,
                "inbound_lead_generation_rate": 5.0,
                "outbound_lead_generation_rate": 3.0,
                "lead_to_c_conversion_rate": 0.2,
                "lead_to_requirement_delay": 1.0,
                "requirement_to_fulfilment_delay": 0.5,
                "avg_order_quantity_initial": 50.0,
                "client_requirement_growth": 0.1,
                "TAM": 1000.0
            }


def _create_direct_market_revenue_dataframe(
    state: DirectMarketRevenueState, 
    sector_product_combinations: List[str]
) -> pd.DataFrame:
    """Create a DataFrame for direct market revenue parameters."""
    
    # Define parameter descriptions
    param_descriptions = {
        "lead_start_year": "Year material begins receiving other-client leads",
        "inbound_lead_generation_rate": "Per quarter inbound leads for the material",
        "outbound_lead_generation_rate": "Per quarter outbound leads for the material",
        "lead_to_c_conversion_rate": "Lead to client conversion (fraction)",
        "lead_to_requirement_delay": "Lead-to-requirement delay for first order (quarters)",
        "requirement_to_fulfilment_delay": "Requirement-to-delivery delay for running requirements (quarters)",
        "avg_order_quantity_initial": "Starting order quantity (units per client)",
        "client_requirement_growth": "Percentage growth of order quantity per quarter",
        "TAM": "Total addressable market for other clients (clients)"
    }
    
    # Create DataFrame
    data = {"Parameter": [], "Description": []}
    for sp in sector_product_combinations:
        data[sp] = []
    
    for param, description in param_descriptions.items():
        data["Parameter"].append(param)
        data["Description"].append(description)
        for sp in sector_product_combinations:
            value = state.direct_market_params.get(sp, {}).get(param, 0.0)
            data[sp].append(value)
    
    return pd.DataFrame(data)


def _update_direct_market_revenue_state(
    state: DirectMarketRevenueState, 
    df: pd.DataFrame, 
    sector_product_combinations: List[str]
):
    """Update the direct market revenue state from the DataFrame."""
    
    for _, row in df.iterrows():
        param = row["Parameter"]
        for sp in sector_product_combinations:
            if sp in df.columns and pd.notna(row[sp]):
                if sp not in state.direct_market_params:
                    state.direct_market_params[sp] = {}
                state.direct_market_params[sp][param] = float(row[sp])


def _check_for_unsaved_changes(state: DirectMarketRevenueState) -> bool:
    """Check if there are any unsaved changes in the state."""
    
    # For now, we'll use the has_unsaved_changes flag
    # In a more sophisticated implementation, we could compare against original values
    return state.has_unsaved_changes


def render_direct_market_revenue_summary(state: DirectMarketRevenueState, sector_product_combinations: List[str]):
    """Render a summary of the current direct market revenue configuration."""
    
    st.markdown("### Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sector-Product Combinations", len(sector_product_combinations))
        if sector_product_combinations:
            st.caption(", ".join(sector_product_combinations[:3]) + ("..." if len(sector_product_combinations) > 3 else ""))
    
    with col2:
        total_params = len(
            state.direct_market_params.get(
                list(state.direct_market_params.keys())[0] 
                if state.direct_market_params else []
            )
        )
        st.metric("Direct Market Parameters", total_params)
        st.caption("Lead generation, conversion rates, delays, etc.")
    
    with col3:
        if sector_product_combinations:
            sample_sp = sector_product_combinations[0]
            if sample_sp in state.direct_market_params:
                sample_tam = state.direct_market_params[sample_sp].get("TAM", 0)
                sample_leads = state.direct_market_params[sample_sp].get("inbound_lead_generation_rate", 0)
                st.metric("Sample TAM", f"{sample_tam:.0f}")
                st.caption(f"Sample leads: {sample_leads:.1f}/quarter")
    
    # Show parameter categories
    st.markdown("**Parameter Categories:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Lead Generation**")
        st.caption("• lead_start_year\n• inbound_lead_generation_rate\n• outbound_lead_generation_rate")
    
    with col2:
        st.markdown("**Conversion & Timing**")
        st.caption("• lead_to_c_conversion_rate\n• lead_to_requirement_delay\n• requirement_to_fulfilment_delay")
    
    with col3:
        st.markdown("**Orders & Growth**")
        st.caption("• avg_order_quantity_initial\n• client_requirement_growth\n• TAM")
    
    # Show some sample values
    if sector_product_combinations:
        sample_sp = sector_product_combinations[0]
        st.markdown(f"**Sample Values for {sample_sp}:**")
        
        if sample_sp in state.direct_market_params:
            sample_tam = state.direct_market_params[sample_sp].get("TAM", 0)
            sample_leads = state.direct_market_params[sample_sp].get(
                "inbound_lead_generation_rate", 0
            )
            sample_conversion = state.direct_market_params[sample_sp].get(
                "lead_to_c_conversion_rate", 0
            )
            st.caption(
                f"TAM: {sample_tam:.0f}, Inbound Leads: {sample_leads:.1f}/quarter, "
                f"Conversion: {sample_conversion:.1%}"
            )
