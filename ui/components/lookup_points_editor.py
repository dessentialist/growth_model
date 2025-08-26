"""
Lookup Points Editor Component

This component provides a user interface for managing time-series lookup points
for production capacity and pricing. It includes table-based input with years
as columns and products as rows, with save button protection.

Author: AI Assistant
Date: 2024
"""

import streamlit as st
import pandas as pd
from typing import List, Dict


from ui.state import LookupPointsState


def render_lookup_points_editor(
    state: LookupPointsState,
    products: List[str],
    start_year: float = 2025.0,
    stop_year: float = 2032.0,
    dt: float = 0.25,
    on_save: callable = None
) -> LookupPointsState:
    """
    Render the lookup points editor for managing time-series production capacity and pricing.
    
    Args:
        state: Current lookup points state
        products: List of products to manage
        start_year: Start year for the simulation
        stop_year: Stop year for the simulation
        dt: Time step in years
        on_save: Optional callback function when changes are saved
        
    Returns:
        Updated lookup points state
    """
    
    st.markdown("### Lookup Points Management")
    st.caption("Manage time-series production capacity and pricing per product per year.")
    
    # Initialize state if empty
    if not products:
        st.warning("⚠️ No products available. Please configure Simulation Definitions first.")
        return state
    
    # Generate year range based on simulation parameters
    years = _generate_year_range(start_year, stop_year, dt)
    
    # Initialize parameters if not already set
    _initialize_lookup_points_state(state, products, years)
    
    # Create tabs for the two parameter types
    tab1, tab2 = st.tabs(["Production Capacity", "Pricing"])
    
    # Tab 1: Production Capacity
    with tab1:
        st.markdown("#### Production Capacity (Units per Year)")
        st.caption("Maximum production capacity for each product per year.")
        
        capacity_df = _create_production_capacity_dataframe(state, products, years)
        updated_capacity = st.data_editor(
            capacity_df,
            key="production_capacity_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Product": st.column_config.TextColumn("Product", disabled=True),
                **{str(year): st.column_config.NumberColumn(str(year), format="%.0f", min_value=0.0) for year in years}
            }
        )
        
        # Update state with changes
        _update_production_capacity_state(state, updated_capacity, products, years)
    
    # Tab 2: Pricing
    with tab2:
        st.markdown("#### Pricing (Price per Unit)")
        st.caption("Price per unit for each product per year.")
        
        pricing_df = _create_pricing_dataframe(state, products, years)
        updated_pricing = st.data_editor(
            pricing_df,
            key="pricing_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Product": st.column_config.TextColumn("Product", disabled=True),
                **{str(year): st.column_config.NumberColumn(str(year), format="%.2f", min_value=0.0) for year in years}
            }
        )
        
        # Update state with changes
        _update_pricing_state(state, updated_pricing, products, years)
    
    # Save button and change tracking
    st.markdown("---")
    
    # Check for unsaved changes
    has_changes = _check_for_unsaved_changes(state)
    state.has_unsaved_changes = has_changes
    
    if has_changes:
        st.warning("⚠️ You have unsaved changes. Click Save to persist your changes.")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Save Changes", type="primary", disabled=not has_changes, key="lookup_points_save_btn"):
            if on_save:
                on_save(state)
            st.success("✅ Lookup points saved successfully!")
            state.has_unsaved_changes = False
            st.rerun()
    
    with col2:
        if has_changes:
            st.caption("Save your changes to prevent data loss.")
        else:
            st.caption("All changes have been saved.")
    
    # Summary section
    render_lookup_points_summary(state, products, years)
    
    return state


def _generate_year_range(start_year: float, stop_year: float, dt: float) -> List[float]:
    """Generate a list of years based on simulation parameters."""
    
    years = []
    current_year = start_year
    while current_year <= stop_year:
        years.append(round(current_year, 2))
        current_year += dt
    
    return years


def _initialize_lookup_points_state(state: LookupPointsState, products: List[str], years: List[float]):
    """Initialize the lookup points state with default values if not already set."""
    
    # Production Capacity
    if not state.production_capacity:
        state.production_capacity = {}
        for product in products:
            state.production_capacity[product] = {}
            for year in years:
                # Default capacity: 1000 units per year, with some growth
                base_capacity = 1000.0
                growth_factor = 1.0 + (year - years[0]) * 0.1  # 10% growth per year
                state.production_capacity[product][year] = base_capacity * growth_factor
    
    # Pricing
    if not state.pricing:
        state.pricing = {}
        for product in products:
            state.pricing[product] = {}
            for year in years:
                # Default price: $100 per unit, with some inflation
                base_price = 100.0
                inflation_factor = 1.0 + (year - years[0]) * 0.02  # 2% inflation per year
                state.pricing[product][year] = base_price * inflation_factor


def _create_production_capacity_dataframe(state: LookupPointsState, products: List[str], years: List[float]) -> pd.DataFrame:
    """Create a DataFrame for production capacity parameters."""
    
    # Create DataFrame
    data = {"Product": []}
    for year in years:
        data[str(year)] = []
    
    for product in products:
        data["Product"].append(product)
        for year in years:
            value = state.production_capacity.get(product, {}).get(year, 0.0)
            data[str(year)].append(value)
    
    return pd.DataFrame(data)


def _create_pricing_dataframe(state: LookupPointsState, products: List[str], years: List[float]) -> pd.DataFrame:
    """Create a DataFrame for pricing parameters."""
    
    # Create DataFrame
    data = {"Product": []}
    for year in years:
        data[str(year)] = []
    
    for product in products:
        data["Product"].append(product)
        for year in years:
            value = state.pricing.get(product, {}).get(year, 0.0)
            data[str(year)].append(value)
    
    return pd.DataFrame(data)


def _update_production_capacity_state(state: LookupPointsState, df: pd.DataFrame, products: List[str], years: List[float]):
    """Update the production capacity state from the DataFrame."""
    
    for _, row in df.iterrows():
        product = row["Product"]
        if product not in state.production_capacity:
            state.production_capacity[product] = {}
        
        for year in years:
            year_str = str(year)
            if year_str in df.columns and pd.notna(row[year_str]):
                state.production_capacity[product][year] = float(row[year_str])


def _update_pricing_state(state: LookupPointsState, df: pd.DataFrame, products: List[str], years: List[float]):
    """Update the pricing state from the DataFrame."""
    
    for _, row in df.iterrows():
        product = row["Product"]
        if product not in state.pricing:
            state.pricing[product] = {}
        
        for year in years:
            year_str = str(year)
            if year_str in df.columns and pd.notna(row[year_str]):
                state.pricing[product][year] = float(row[year_str])


def _check_for_unsaved_changes(state: LookupPointsState) -> bool:
    """Check if there are any unsaved changes in the state."""
    
    # For now, we'll use the has_unsaved_changes flag
    # In a more sophisticated implementation, we could compare against original values
    return state.has_unsaved_changes


def render_lookup_points_summary(state: LookupPointsState, products: List[str], years: List[float]):
    """Render a summary of the current lookup points configuration."""
    
    st.markdown("### Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Products", len(products))
        if products:
            st.caption(", ".join(products[:3]) + ("..." if len(products) > 3 else ""))
    
    with col2:
        st.metric("Years", len(years))
        st.caption(f"{years[0]} to {years[-1]} ({len(years)} time steps)")
    
    with col3:
        total_capacity_points = sum(len(state.production_capacity.get(p, {})) for p in products)
        total_pricing_points = sum(len(state.pricing.get(p, {})) for p in products)
        st.metric("Data Points", total_capacity_points + total_pricing_points)
        st.caption("Capacity + Pricing")
    
    # Show data coverage information
    if products and years:
        total_capacity_points = sum(len(state.production_capacity.get(p, {})) for p in products)
        total_pricing_points = sum(len(state.pricing.get(p, {})) for p in products)
        total_possible_points = len(products) * len(years) * 2  # 2 types: capacity + pricing
        
        coverage_percentage = (total_capacity_points + total_pricing_points) / total_possible_points * 100 if total_possible_points > 0 else 0
        
        st.info(f"📊 Data Coverage: {coverage_percentage:.1f}% ({total_capacity_points + total_pricing_points}/{total_possible_points} points)")
        st.caption("Configure all time-series points for complete production and pricing modeling")
    else:
        st.info("📊 No products or years available. Configure simulation definitions and runspecs first.")


def get_lookup_points_for_yaml(state: LookupPointsState) -> Dict:
    """Convert lookup points state to YAML-compatible format for backend integration."""
    
    yaml_data = {}
    
    # Production capacity lookup tables
    for product, year_data in state.production_capacity.items():
        lookup_name = f"max_capacity_{product}"
        yaml_data[lookup_name] = [[year, capacity] for year, capacity in year_data.items()]
    
    # Pricing lookup tables
    for product, year_data in state.pricing.items():
        lookup_name = f"price_{product}"
        yaml_data[lookup_name] = [[year, price] for year, price in year_data.items()]
    
    return yaml_data
