"""
Simulation Definitions Editor Component

This component provides a user interface for managing the market, sector, and product lists
that define the simulation universe. It includes add/delete functionality with save button protection.

Author: AI Assistant
Date: 2024
"""

import streamlit as st

from ui.state import SimulationDefinitionsState


def render_simulation_definitions_editor(
    state: SimulationDefinitionsState,
    on_save: callable = None
) -> SimulationDefinitionsState:
    """
    Render the simulation definitions editor for managing markets, sectors, and products.
    
    Args:
        state: Current simulation definitions state
        on_save: Optional callback function when changes are saved
        
    Returns:
        Updated simulation definitions state
    """
    st.markdown("### Market List")
    st.caption("Define the markets available in your simulation.")

    col1, col2 = st.columns([3, 1])
    with col1:
        new_market = st.text_input(
            "Add New Market",
            placeholder="Enter market name...",
            key="new_market_input"
        )
    with col2:
        add_market_btn = st.button("Add Market", key="add_market_btn")

    if add_market_btn and new_market.strip():
        market_name = new_market.strip()
        if market_name and market_name not in state.markets:
            state.markets.append(market_name)
            st.success(f"Added market: {market_name}")
            st.rerun()
        elif market_name in state.markets:
            st.error(f"Market '{market_name}' already exists.")

    if state.markets:
        st.markdown("**Current Markets:**")
        cols = st.columns(len(state.markets))
        for i, market in enumerate(state.markets):
            with cols[i]:
                st.text(f"**{market}**")
                if st.button("Delete", key=f"del_market_{i}", type="secondary"):
                    state.markets.pop(i)
                    st.success(f"Removed market: {market}")
                    st.rerun()

    st.markdown("---")

    st.markdown("### Sector List")
    st.caption("Define the sectors available in your simulation.")

    col1, col2 = st.columns([3, 1])
    with col1:
        new_sector = st.text_input(
            "Add New Sector",
            placeholder="Enter sector name...",
            key="new_sector_input"
        )
    with col2:
        add_sector_btn = st.button("Add Sector", key="add_sector_btn")

    if add_sector_btn and new_sector.strip():
        sector_name = new_sector.strip()
        if sector_name and sector_name not in state.sectors:
            state.sectors.append(sector_name)
            st.success(f"Added sector: {sector_name}")
            st.rerun()
        elif sector_name in state.sectors:
            st.error(f"Sector '{sector_name}' already exists.")

    if state.sectors:
        st.markdown("**Current Sectors:**")
        cols = st.columns(len(state.sectors))
        for i, sector in enumerate(state.sectors):
            with cols[i]:
                st.text(f"**{sector}**")
                if st.button("Delete", key=f"del_sector_{i}", type="secondary"):
                    state.sectors.pop(i)
                    st.success(f"Removed sector: {sector}")
                    st.rerun()

    st.markdown("---")

    st.markdown("### Product List")
    st.caption("Define the products available in your simulation.")

    col1, col2 = st.columns([3, 1])
    with col1:
        new_product = st.text_input(
            "Add New Product",
            placeholder="Enter product name...",
            key="new_product_input"
        )
    with col2:
        add_product_btn = st.button("Add Product", key="add_product_btn")

    if add_product_btn and new_product.strip():
        product_name = new_product.strip()
        if product_name and product_name not in state.products:
            state.products.append(product_name)
            st.success(f"Added product: {product_name}")
            st.rerun()
        elif product_name in state.products:
            st.error(f"Product '{product_name}' already exists.")

    if state.products:
        st.markdown("**Current Products:**")
        cols = st.columns(len(state.products))
        for i, product in enumerate(state.products):
            with cols[i]:
                st.text(f"**{product}**")
                if st.button("Delete", key=f"del_product_{i}", type="secondary"):
                    state.products.pop(i)
                    st.success(f"Removed product: {product}")
                    st.rerun()

    st.markdown("---")

    # Summary section
    render_simulation_definitions_summary(state)

    return state


def render_simulation_definitions_summary(state: SimulationDefinitionsState):
    """
    Render a summary of the current simulation definitions.
    
    Args:
        state: Current simulation definitions state
    """
    st.markdown("### Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Markets", len(state.markets))
        if state.markets:
            st.caption(", ".join(state.markets[:3]) + ("..." if len(state.markets) > 3 else ""))
    
    with col2:
        st.metric("Sectors", len(state.sectors))
        if state.sectors:
            st.caption(", ".join(state.sectors[:3]) + ("..." if len(state.sectors) > 3 else ""))
    
    with col3:
        st.metric("Products", len(state.products))
        if state.products:
            st.caption(", ".join(state.products[:3]) + ("..." if len(state.products) > 3 else ""))
