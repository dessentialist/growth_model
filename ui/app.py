"""
Growth Model UI - Main Application

This is the main Streamlit application for the Growth Model UI.
It provides a comprehensive interface for managing simulation scenarios,
running simulations, and viewing results.

Author: AI Assistant
Date: 2024
"""

import streamlit as st
from pathlib import Path

# Import the bundle and UI components
from src.phase1_data import load_phase1_inputs

# Import UI components
from ui.components.simulation_definitions_editor import render_simulation_definitions_editor
from ui.components.runspecs_form import render_runspecs_form
from ui.components.primary_map_editor import render_primary_map_editor
from ui.components.client_revenue_editor import render_client_revenue_editor
from ui.components.direct_market_revenue_editor import render_direct_market_revenue_editor
from ui.components.lookup_points_editor import render_lookup_points_editor
from ui.components.runner_tab import render_runner_tab
from ui.components.logs_tab import render_logs_tab

# Import state
from ui.state import UIState

# Page configuration
st.set_page_config(
    page_title="Growth Model UI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize the bundle
@st.cache_resource
def load_bundle():
    """Load the phase 1 data bundle once and cache it."""
    return load_phase1_inputs()

bundle = load_bundle()

# Initialize UI state
if "ui_state" not in st.session_state:
    st.session_state["ui_state"] = UIState()

ui_state: UIState = st.session_state["ui_state"]

# Callback functions for save operations
def on_runspecs_save(updated_runspecs):
    """Callback when runspecs are saved."""
    ui_state.runspecs = updated_runspecs
    st.session_state["ui_state"] = ui_state

def on_primary_map_save(updated_primary_map):
    """Callback when primary map is saved."""
    ui_state.primary_map = updated_primary_map
    st.session_state["ui_state"] = ui_state

def on_client_revenue_save(updated_client_revenue):
    """Callback when client revenue is saved."""
    ui_state.client_revenue = updated_client_revenue
    st.session_state["ui_state"] = ui_state

def on_direct_market_revenue_save(updated_direct_market_revenue):
    """Callback when direct market revenue is saved."""
    ui_state.direct_market_revenue = updated_direct_market_revenue
    st.session_state["ui_state"] = ui_state

def on_lookup_points_save(updated_lookup_points):
    """Callback when lookup points are saved."""
    ui_state.lookup_points = updated_lookup_points
    st.session_state["ui_state"] = ui_state

def on_runner_save(updated_runner):
    """Callback when runner settings are saved."""
    ui_state.runner = updated_runner
    st.session_state["ui_state"] = ui_state

def on_logs_save(updated_logs):
    """Callback when log settings are saved."""
    ui_state.logs = updated_logs
    st.session_state["ui_state"] = ui_state

# Helper function to extract sector-product combinations
def get_sector_product_combinations(bundle):
    """Extracts all unique sector-product combinations from the bundle."""
    all_combinations = []
    if hasattr(bundle, 'lists') and hasattr(bundle.lists, 'sectors') and hasattr(bundle.lists, 'products'):
        for sector in bundle.lists.sectors:
            for product in bundle.lists.products:
                all_combinations.append(f"{sector}_{product}")
    return all_combinations

# Main application
def main():
    """Main application function."""
    st.title("📈 Growth Model UI")
    st.caption("Scenario Editor & Runner")
    
    # Create the new 8-tab structure
    tabs = st.tabs([
        "Simulation Definitions",  # Tab 1: Market/Sector/Product list management
        "Simulation Specs",        # Tab 2: Runtime controls and scenario management
        "Primary Mapping",         # Tab 3: Sector-product mapping with insights
        "Client Revenue",          # Tab 4: Comprehensive parameter tables (19 parameters)
        "Direct Market Revenue",   # Tab 5: Product-specific parameters (9 parameters)
        "Lookup Points",           # Tab 6: Time-series production capacity and pricing
        "Runner",                  # Tab 7: Scenario execution and monitoring
        "Logs"                     # Tab 8: Simulation logs and monitoring
    ])
    
    # Tab 1: Simulation Definitions
    with tabs[0]:
        st.header("Simulation Definitions")
        st.caption("Manage the market, sector, and product lists that define your simulation universe.")
        
        # User Guide
        st.info("**📖 How to use this page:** Define your simulation universe by setting up markets, sectors, and products. Start with the basic lists - you can add or remove items as needed. These definitions will be used across all other tabs to create dynamic parameter tables and mappings. Changes here will automatically update related components in other tabs.")

        # Initialize simulation definitions from bundle if not already set
        if not ui_state.simulation_definitions.markets:
            ui_state.simulation_definitions.markets = ["Global"]
        if not ui_state.simulation_definitions.sectors:
            ui_state.simulation_definitions.sectors = (
                bundle.lists.sectors[:8] if hasattr(bundle.lists, 'sectors') 
                else ["Sector_One", "Sector_Two"]
            )
        if not ui_state.simulation_definitions.products:
            ui_state.simulation_definitions.products = (
                bundle.lists.products[:8] if hasattr(bundle.lists, 'products') 
                else ["Product_One", "Product_Two"]
            )

        # Render the simulation definitions editor
        ui_state.simulation_definitions = render_simulation_definitions_editor(
            ui_state.simulation_definitions
        )
    
    # Tab 2: Simulation Specs (Phase 3 - Enhanced)
    with tabs[1]:
        st.header("Simulation Specs")
        st.caption("Runtime controls and scenario management with save protection.")
        
        # User Guide
        st.info("**📖 How to use this page:** Configure your simulation runtime parameters including start/stop years, time step, and scenario settings. Use the 'Save' button to persist your changes. The form validates inputs and shows errors if any values are invalid. These specs control how your simulation runs and what data is generated.")
        
        # Render the enhanced runspecs form
        updated_runspecs, errors = render_runspecs_form(
            ui_state.runspecs,
            bundle=bundle,
            on_save_callback=on_runspecs_save
        )
        
        # Update the state if there are no errors
        if not errors:
            ui_state.runspecs = updated_runspecs
    
    # Tab 3: Primary Mapping (Phase 4 - Enhanced)
    with tabs[2]:
        st.header("Primary Mapping")
        st.caption("Sector-product mapping with insights and dynamic table generation.")
        
        # User Guide
        st.info("**📖 How to use this page:** Map sectors to products to define which combinations are valid in your simulation. Use the 'Add Mapping' button to create new sector-product relationships. The table shows existing mappings with insights into parameter coverage. This mapping determines which combinations appear in the Client Revenue and Direct Market Revenue tabs.")
        
        # Render the enhanced primary map editor
        updated_primary_map = render_primary_map_editor(
            ui_state.primary_map,
            bundle=bundle,
            on_save_callback=on_primary_map_save
        )
        
        # Update the state
        ui_state.primary_map = updated_primary_map
    
    # Tab 4: Client Revenue (Phase 5 - Implemented)
    with tabs[3]:
        st.header("Client Revenue")
        st.caption("Comprehensive parameter tables (19 parameters) organized by sector-product combinations.")
        
        # User Guide
        st.info("**📖 How to use this page:** Configure 19 client revenue parameters across three categories: Market Activation (9 params), Orders (9 params), and Seeds (3 params). Each parameter is organized by sector-product combinations from your Primary Mapping. Use the tabs to switch between parameter groups. Click 'Save' after making changes. These parameters control client acquisition, order behavior, and initial seeding.")
        
        # Get sector-product combinations for dynamic content
        sector_product_combinations = get_sector_product_combinations(bundle)
        
        # Render the client revenue editor
        updated_client_revenue = render_client_revenue_editor(
            ui_state.client_revenue,
            sector_product_combinations=sector_product_combinations,
            on_save=on_client_revenue_save
        )
        
        # Update the state
        ui_state.client_revenue = updated_client_revenue
    
    # Tab 5: Direct Market Revenue (Phase 6 - Implemented)
    with tabs[4]:
        st.header("Direct Market Revenue")
        st.caption("Product-specific parameters (9 parameters) organized by sector-product combinations.")
        
        # User Guide
        st.info("**📖 How to use this page:** Configure 9 product-specific parameters for direct market revenue calculations. These parameters are organized by sector-product combinations and control pricing, capacity, and market dynamics. Use the 'Add Parameter' button to create new parameters or edit existing ones. Remember to save your changes after configuration.")
        
        # Get sector-product combinations for dynamic content
        sector_product_combinations = get_sector_product_combinations(bundle)
        
        # Render the direct market revenue editor
        updated_direct_market_revenue = render_direct_market_revenue_editor(
            ui_state.direct_market_revenue,
            sector_product_combinations=sector_product_combinations,
            on_save=on_direct_market_revenue_save
        )
        
        # Update the state
        ui_state.direct_market_revenue = updated_direct_market_revenue
    
    # Tab 6: Lookup Points (Phase 7 - Implemented)
    with tabs[5]:
        st.header("Lookup Points")
        st.caption("Time-series production capacity and pricing per product per year.")
        
        # User Guide
        st.info("**📖 How to use this page:** Define time-series data for production capacity and pricing across your simulation timeline. Set values for each product and year combination. Use the 'Add Year' button to extend the timeline or 'Add Product' for new products. This data is used during simulation execution to determine capacity constraints and pricing dynamics over time.")
        
        # Get products from simulation definitions
        products = ui_state.simulation_definitions.products
        
        # Get simulation time parameters from runspecs
        start_year = ui_state.runspecs.starttime
        stop_year = ui_state.runspecs.stoptime
        dt = ui_state.runspecs.dt
        
        # Render the lookup points editor
        updated_lookup_points = render_lookup_points_editor(
            ui_state.lookup_points,
            products=products,
            start_year=start_year,
            stop_year=stop_year,
            dt=dt,
            on_save=on_lookup_points_save
        )
        
        # Update the state
        ui_state.lookup_points = updated_lookup_points
    
    # Tab 7: Runner (Phase 8 - Implemented)
    with tabs[6]:
        st.header("Runner")
        st.caption("Scenario execution and monitoring with full backend integration, real-time results display, and comprehensive file management.")
        
        # User Guide
        st.info("**📖 How to use this page:** Execute your configured scenarios and monitor simulation progress. Select a scenario name, configure execution settings (debug mode, plot generation, KPI options), then click 'Run Simulation'. Monitor real-time progress and view results including CSV data and generated plots. Use the execution history to track previous runs and access their outputs.")
        
        # Render the runner tab
        updated_runner = render_runner_tab(
            ui_state.runner,
            on_save=on_runner_save
        )
        
        # Update the state
        ui_state.runner = updated_runner
    
    # Tab 8: Logs (Phase 8 - Implemented)
    with tabs[7]:
        st.header("Logs")
        st.caption("Real simulation logs from the simulation engine with comprehensive parsing, filtering, and export capabilities.")
        
        # User Guide
        st.info("**📖 How to use this page:** View and analyze real simulation logs from your executed scenarios. Use the filters to search for specific log entries by level, source, or text content. The logs show detailed execution information, errors, warnings, and performance metrics. Export logs for external analysis or troubleshooting. This is essential for debugging simulation issues and understanding execution behavior.")
        
        # Render the logs tab
        updated_logs = render_logs_tab(
            ui_state.logs,
            on_save=on_logs_save
        )
        
        # Update the state
        ui_state.logs = updated_logs
    


if __name__ == "__main__":
    main()
