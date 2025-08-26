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
import sys

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import the bundle and UI components
from phase1_data import load_phase1_inputs
from ui.services.validation_client import get_permissible_keys, try_validate_scenario_dict

# Import UI components
from ui.components.simulation_definitions_editor import render_simulation_definitions_editor
from ui.components.constants_editor import render_constants_editor
from ui.components.points_editor import render_points_editor
from ui.components.seeds_editor import render_seeds_editor
from ui.components.runspecs_form import render_runspecs_form
from ui.components.primary_map_editor import render_primary_map_editor
from ui.components.client_revenue_editor import render_client_revenue_editor
from ui.components.direct_market_revenue_editor import render_direct_market_revenue_editor

# Import services
from ui.services.builder import (
    write_scenario_yaml,
)

# Import state
from ui.state import UIState

# Page configuration
st.set_page_config(
    page_title="Growth Model UI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
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
    
    # Tab 6: Lookup Points (placeholder for Phase 7)
    with tabs[5]:
        st.header("Lookup Points")
        st.caption("Time-series production capacity and pricing.")
        st.info("🚧 This tab will be implemented in Phase 7.")
    
    # Tab 7: Runner (placeholder for Phase 8)
    with tabs[6]:
        st.header("Runner")
        st.caption("Scenario execution and monitoring.")
        st.info("🚧 This tab will be implemented in Phase 8.")
    
    # Tab 8: Logs (placeholder for Phase 8)
    with tabs[7]:
        st.header("Logs")
        st.caption("Simulation logs and monitoring.")
        st.info("🚧 This tab will be implemented in Phase 8.")
    
    # Legacy Functions in Sidebar (temporarily moved here)
    with st.sidebar:
        st.header("Legacy Functions")
        st.caption("These functions will be integrated into the new tab structure.")
        
        # Constants editor (moved from Tab 2)
        st.subheader("Constants Overrides")
        perms = get_permissible_keys(
            bundle,
            anchor_mode=ui_state.runspecs.anchor_mode,
            extra_pairs=extra_pairs or None,
        )
        ui_state.overrides = render_constants_editor(ui_state.overrides, perms.constants)
        
        # Points editor (moved from Tab 3)
        st.subheader("Points Overrides")
        perms = get_permissible_keys(bundle, anchor_mode=ui_state.runspecs.anchor_mode)
        ui_state.overrides = render_points_editor(ui_state.overrides, perms.points)
        
        # Seeds editor (moved from Tab 4)
        st.subheader("Seeds Configuration")
        ui_state.seeds = render_seeds_editor(ui_state.seeds, bundle, ui_state.runspecs.anchor_mode)
        
        # Validate & Save (moved from Tab 5)
        st.subheader("Validate & Save")
        scenario_dict = ui_state.to_scenario_dict_normalized()
        ok, err = try_validate_scenario_dict(bundle, scenario_dict)
        if ok:
            st.success("✅ Scenario validates")
        else:
            st.error(f"❌ Validation error: {err}")
        
        # Run Controls
        st.markdown("---")
        st.header("Run Controls")
        
        # Run Preset
        st.subheader("Run Preset")
        preset_scenario = st.selectbox(
            "Select Scenario",
            ["baseline", "high_capacity", "price_shock", "working_scenario"],
            key="preset_scenario"
        )
        
        if st.button("Run Preset", key="run_preset_btn"):
            with st.spinner(f"Running {preset_scenario}..."):
                # Run the preset scenario
                pass
        
        # Validate, Save, and Run Current
        st.subheader("Current Scenario")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Validate", key="validate_btn"):
                scenario_dict = ui_state.to_scenario_dict_normalized()
                ok, err = try_validate_scenario_dict(bundle, scenario_dict)
                if ok:
                    st.success("✅ Scenario validates")
                else:
                    st.error(f"❌ Validation error: {err}")
        
        with col2:
            if st.button("Save", key="save_btn"):
                scenario_dict = ui_state.to_scenario_dict_normalized()
                scenario_name = ui_state.name
                scenario_path = Path("scenarios") / f"{scenario_name}.yaml"
                
                try:
                    write_scenario_yaml(scenario_dict, scenario_path)
                    st.success(f"✅ Scenario saved to {scenario_path}")
                except Exception as e:
                    st.error(f"❌ Error saving scenario: {e}")
        
        if st.button("Run Current", key="run_current_btn", type="primary"):
            with st.spinner("Running current scenario..."):
                # Run the current scenario
                pass
    
    # Main content area info
    st.markdown("---")
    st.info(
        "🎯 **New UI Structure**: This interface has been restructured with 8 tabs for better "
        "organization. Phases 1-6 are now complete with enhanced functionality including "
        "save protection, change tracking, dynamic table generation, and comprehensive "
        "parameter management. Legacy functions are temporarily available in the sidebar "
        "and will be integrated into their respective tabs in future phases."
    )

if __name__ == "__main__":
    # Get extra pairs for validation
    extra_pairs = None
    if hasattr(bundle, 'lists') and hasattr(bundle.lists, 'sectors') and hasattr(bundle.lists, 'products'):
        extra_pairs = [(s, p) for s in bundle.lists.sectors for p in bundle.lists.products]
    
    main()
