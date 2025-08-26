from __future__ import annotations

"""
Streamlit UI — Growth Model with New Tab Structure and Framework-Agnostic Architecture.

This is the Phase 1 implementation with:
- New tab structure: Runner, Mapping, Logs, Output, Parameters, Points, Seeds
- Framework-agnostic business logic in src/ui_logic/
- Reactive state management
- Complete separation of UI and business logic
"""

import time
from pathlib import Path
import sys
import io

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import streamlit as st

# Import framework-agnostic business logic
from src.ui_logic import StateManager, ScenarioManager, ValidationManager, RunnerManager, DataManager
from src.ui_logic.state_manager import TabType, PrimaryMapState, PrimaryMapEntry, ScenarioOverridesState

# Import existing data loading system
from src.phase1_data import load_phase1_inputs
from src.scenario_loader import list_permissible_override_keys

st.set_page_config(page_title="Growth System – Scenario Runner", layout="wide")

st.title("Growth System – Scenario Editor & Runner")

# Initialize business logic managers
@st.cache_resource(show_spinner=False)
def _initialize_managers():
    """Initialize all business logic managers."""
    state_manager = StateManager()
    data_manager = DataManager(state_manager, _PROJECT_ROOT)
    validation_manager = ValidationManager(state_manager, data_manager)
    scenario_manager = ScenarioManager(_PROJECT_ROOT / "scenarios", state_manager)
    runner_manager = RunnerManager(state_manager, _PROJECT_ROOT)
    
    return state_manager, data_manager, validation_manager, scenario_manager, runner_manager

# Initialize managers
state_manager, data_manager, validation_manager, scenario_manager, runner_manager = _initialize_managers()

# Load Phase1Bundle for data access
@st.cache_resource(show_spinner=False)
def _load_phase1_bundle():
    """Load Phase1Bundle for data access."""
    try:
        bundle = load_phase1_inputs()
        return bundle
    except Exception as e:
        st.error(f"Failed to load inputs.json: {e}")
        return None

# Load the bundle
phase1_bundle = _load_phase1_bundle()

# Initialize session state
if "ui_state" not in st.session_state:
    st.session_state["ui_state"] = state_manager.get_state()

# Get current state
ui_state = st.session_state["ui_state"]

# Tab navigation
tab_names = ["Runner", "Mapping", "Logs", "Output", "Parameters", "Points", "Seeds"]
tab_enum_map = {
    "Runner": TabType.RUNNER,
    "Mapping": TabType.MAPPING,
    "Logs": TabType.LOGS,
    "Output": TabType.OUTPUT,
    "Parameters": TabType.PARAMETERS,
    "Points": TabType.POINTS,
    "Seeds": TabType.SEEDS
}

# Create tabs
tabs = st.tabs(tab_names)

# Runner Tab
with tabs[0]:
    st.header("Runner")
    
    # Enhanced Scenario Management
    st.subheader("Scenario Management")
    
    # Load existing scenarios
    scenarios = scenario_manager.list_available_scenarios()
    if scenarios:
        scenario_names = [s.stem for s in scenarios]
        
        # Scenario selection and management
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_scenario = st.selectbox("Available scenarios", scenario_names, key="scenario_select")
        with col2:
            st.metric("Total Scenarios", len(scenarios))
        
        # Scenario actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📂 Load Scenario", type="primary", use_container_width=True):
                with st.spinner(f"Loading {selected_scenario}..."):
                    success, error = scenario_manager.load_scenario_into_state(selected_scenario)
                    if success:
                        st.success(f"✅ Loaded scenario: {selected_scenario}")
                        # Update session state
                        st.session_state["ui_state"] = state_manager.get_state()
                        st.rerun()
                    else:
                        st.error(f"❌ Error loading scenario: {error}")
        
        with col2:
            if st.button("🔄 Refresh List", type="secondary", use_container_width=True):
                st.rerun()
        
        with col3:
            if st.button("🗑️ Delete Scenario", type="secondary", use_container_width=True):
                st.warning("Delete functionality not yet implemented")
        
        # Scenario duplication
        st.markdown("---")
        st.markdown("**Duplicate Scenario**")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_name = st.text_input("Duplicate as", value=f"copy_of_{selected_scenario}", key="duplicate_name")
        with col2:
            if st.button("📋 Duplicate", type="secondary", use_container_width=True):
                if new_name and new_name != selected_scenario:
                    with st.spinner(f"Duplicating {selected_scenario}..."):
                        success, error, path = scenario_manager.duplicate_scenario(selected_scenario, new_name)
                        if success:
                            st.success(f"✅ Duplicated to {path}")
                            st.rerun()
                        else:
                            st.error(f"❌ Error duplicating: {error}")
                else:
                    st.error("Please provide a different name for the duplicate")
        
        # Scenario information
        if selected_scenario:
            st.markdown("---")
            st.markdown(f"**Scenario: {selected_scenario}**")
            
            # Get scenario file info
            scenario_file = next((s for s in scenarios if s.stem == selected_scenario), None)
            if scenario_file:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File Size", f"{scenario_file.stat().st_size / 1024:.1f} KB")
                with col2:
                    st.metric("Modified", scenario_file.stat().st_mtime)
                with col3:
                    st.metric("Type", scenario_file.suffix)
    else:
        st.info("📁 No scenarios found. Create scenarios in other tabs or save the current configuration.")
        
        # Quick scenario creation
        st.markdown("---")
        st.markdown("**Quick Scenario Creation**")
        quick_name = st.text_input("Scenario name", value="new_scenario", key="quick_scenario_name")
        if st.button("💾 Save Current as Scenario", type="primary"):
            if quick_name:
                with st.spinner(f"Saving {quick_name}..."):
                    success, error, path = scenario_manager.save_current_state_as_scenario(quick_name, overwrite=False)
                    if success:
                        st.success(f"✅ Scenario saved to {path}")
                        st.rerun()
                    else:
                        st.error(f"❌ Error saving scenario: {error}")
            else:
                st.error("Please provide a scenario name")
    
    # Enhanced Run Controls
    st.subheader("Run Controls")
    
    # Mode toggle integration
    st.markdown("**Mode Configuration**")
    current_mode = ui_state.runspecs.anchor_mode
    mode_col1, mode_col2 = st.columns([2, 2])
    
    with mode_col1:
        st.markdown(f"**Current Mode:** {current_mode.upper()}")
        if current_mode == "sector":
            st.info("🔧 **Sector Mode**: Parameters are configured per sector")
        else:
            st.info("🔧 **SM Mode**: Parameters are configured per sector+product combination")
    
    with mode_col2:
        if st.button("🔄 Switch Mode", type="secondary", use_container_width=True):
            new_mode = "sm" if current_mode == "sector" else "sector"
            state_manager.update_runspecs(anchor_mode=new_mode)
            st.session_state["ui_state"] = state_manager.get_state()
            st.success(f"✅ Switched to {new_mode.upper()} mode")
            st.rerun()
    
    st.markdown("---")
    
    # Preset runner
    st.markdown("**Run Preset Scenario**")
    preset_name = st.text_input("Preset name", value=ui_state.runner.current_preset, key="preset_name")
    
    # Run parameters in organized columns
    st.markdown("**Run Parameters**")
    param_col1, param_col2, param_col3 = st.columns(3)
    
    with param_col1:
        st.markdown("**Execution Options**")
        debug_mode = st.checkbox("🐛 Debug mode", value=ui_state.runner.debug_mode, key="debug_mode")
        visualize = st.checkbox("📊 Generate plots", value=ui_state.runner.visualize, key="visualize")
    
    with param_col2:
        st.markdown("**KPI Generation**")
        kpi_sm_revenue = st.checkbox(
            "💰 Per-(s,m) revenue rows", 
            value=ui_state.runner.kpi_sm_revenue_rows, 
            key="kpi_sm_revenue"
        )
        kpi_sm_clients = st.checkbox(
            "👥 Per-(s,m) client rows", 
            value=ui_state.runner.kpi_sm_client_rows, 
            key="kpi_sm_clients"
        )
    
    with param_col3:
        st.markdown("**Performance**")
        st.info("⚡ Performance monitoring enabled")
        st.caption("Real-time progress tracking")
    
    # Run button with enhanced feedback
    run_col1, run_col2 = st.columns([3, 1])
    with run_col1:
        if st.button("🚀 Run Preset Simulation", type="primary", use_container_width=True):
            with st.spinner("Starting simulation..."):
                # Update runner state
                state_manager.update_runner_state(
                    current_preset=preset_name,
                    debug_mode=debug_mode,
                    visualize=visualize,
                    kpi_sm_revenue_rows=kpi_sm_revenue,
                    kpi_sm_client_rows=kpi_sm_clients
                )
                
                # Run simulation
                success, error = runner_manager.run_preset(
                    preset_name, debug_mode, visualize, kpi_sm_revenue, kpi_sm_clients
                )
                
                if success:
                    st.success("✅ Simulation started successfully!")
                    st.info("Switch to the Logs tab to monitor progress")
                else:
                    st.error(f"❌ Error starting simulation: {error}")
    
    with run_col2:
        if st.button("📋 Show Command", type="secondary", use_container_width=True):
            st.info("Command preview functionality not yet implemented")
    
    # Mode-specific parameter validation
    st.markdown("---")
    st.markdown("**Mode-Specific Validation**")
    
    if current_mode == "sector":
        st.info("✅ **Sector Mode**: Validating sector-level parameters...")
        # Add sector-specific validation here
    else:
        st.info("✅ **SM Mode**: Validating sector+product parameters...")
        # Add SM-specific validation here
    
    # Quick parameter summary
    st.markdown("---")
    st.markdown("**Parameter Summary**")
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Debug Mode", "ON" if debug_mode else "OFF")
    with summary_col2:
        st.metric("Visualization", "ON" if visualize else "OFF")
    with summary_col3:
        kpi_count = sum([kpi_sm_revenue, kpi_sm_clients])
        st.metric("KPI Options", kpi_count)
    
    # Current scenario runner
    st.markdown("**Run Current Scenario**")
    
    # Enhanced validation with real-time feedback
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Validate Current Scenario", type="secondary"):
            # Validate current scenario
            permissible_keys = data_manager.get_permissible_keys(
                ui_state.runspecs.anchor_mode
            )
            validation_result = validation_manager.validate_current_state({
                'constants': permissible_keys.constants,
                'points': permissible_keys.points,
                'sectors': permissible_keys.sectors,
                'products': permissible_keys.products
            })
            
            # Store validation result in session state for display
            st.session_state["last_validation"] = validation_result
    
    with col2:
        if st.button("Validate, Save, and Run Current Scenario", type="primary"):
            # Validate current scenario
            permissible_keys = data_manager.get_permissible_keys(
                ui_state.runspecs.anchor_mode
            )
            validation_result = validation_manager.validate_current_state({
                'constants': permissible_keys.constants,
                'points': permissible_keys.points,
                'sectors': permissible_keys.sectors,
                'products': permissible_keys.products
            })
            
            if not validation_result.is_valid:
                st.error("❌ Scenario validation failed:")
                for error in validation_result.errors[:5]:  # Show first 5 errors
                    st.error(f"- {error.field}: {error.message}")
                if len(validation_result.errors) > 5:
                    st.error(f"... and {len(validation_result.errors) - 5} more errors")
            else:
                st.success("✅ Scenario validation passed!")
                
                # Save and run
                scenario_name = ui_state.name or "working_scenario"
                success, error, path = scenario_manager.save_current_state_as_scenario(scenario_name, overwrite=True)
                
                if success:
                    st.success(f"💾 Scenario saved to {path}")
                    
                    # Run simulation
                    run_success, run_error = runner_manager.run_current_scenario(
                        debug_mode, visualize, kpi_sm_revenue, kpi_sm_clients
                    )
                    
                    if run_success:
                        st.success("🚀 Simulation started successfully")
                    else:
                        st.error(f"❌ Error starting simulation: {run_error}")
                else:
                    st.error(f"❌ Error saving scenario: {error}")
    
    # Display validation results if available
    if "last_validation" in st.session_state:
        validation_result = st.session_state["last_validation"]
        
        if validation_result.is_valid:
            st.success("✅ **Validation Status: PASSED**")
            st.info("All validations passed successfully!")
        else:
            st.error("❌ **Validation Status: FAILED**")
            
            # Group errors by severity
            errors = validation_result.get_errors_by_severity("error")
            warnings = validation_result.get_errors_by_severity("warning")
            info = validation_result.get_errors_by_severity("info")
            
            if errors:
                st.error(f"**Errors ({len(errors)}):**")
                for error in errors[:10]:  # Show first 10 errors
                    st.error(f"- {error.field}: {error.message}")
                if len(errors) > 10:
                    st.error(f"... and {len(errors) - 10} more errors")
            
            if warnings:
                st.warning(f"**Warnings ({len(warnings)}):**")
                for warning in warnings[:5]:  # Show first 5 warnings
                    st.warning(f"- {warning.field}: {warning.message}")
                if len(warnings) > 5:
                    st.warning(f"... and {len(warnings) - 5} more warnings")
            
            if info:
                st.info(f"**Info ({len(info)}):**")
                for info_item in info[:3]:  # Show first 3 info items
                    st.info(f"- {info_item.field}: {info_item.message}")
                if len(info_item) > 3:
                    st.info(f"... and {len(info_item) - 3} more info items")
    
    # Enhanced Simulation Status
    st.subheader("Simulation Status")
    status = runner_manager.get_simulation_status()
    
    # Status overview with better visual feedback
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if status.is_running:
            st.success("🔄 **RUNNING**")
            st.metric("Status", "Active", delta="Running")
        elif status.exit_code is not None:
            if status.exit_code == 0:
                st.success("✅ **COMPLETED**")
                st.metric("Status", "Success", delta="Completed")
            else:
                st.error("❌ **FAILED**")
                st.metric("Status", "Failed", delta=f"Exit: {status.exit_code}")
        else:
            st.info("⏸️ **IDLE**")
            st.metric("Status", "Ready", delta="No simulation")
    
    with col2:
        if status.is_running:
            if status.start_time:
                elapsed = time.time() - status.start_time
                st.metric("Elapsed Time", f"{elapsed:.1f}s")
            if status.progress > 0:
                st.metric("Progress", f"{status.progress:.1%}")
        elif status.exit_code is not None:
            if status.start_time:
                total_time = time.time() - status.start_time
                st.metric("Total Time", f"{total_time:.1f}s")
    
    with col3:
        if status.is_running:
            st.metric("PID", str(status.process_id))
    
    # Detailed status information
    if status.is_running:
        st.markdown("---")
        
        # Progress bar
        if status.progress > 0:
            st.progress(status.progress, text=f"Progress: {status.progress:.1%}")
        
        # Current step information
        if status.current_step:
            st.info(f"**Current Step:** {status.current_step}")
        
        # Auto-refresh for running simulations
        if st.button("🔄 Refresh Status", key="refresh_status"):
            st.rerun()
        
        # Auto-refresh every 5 seconds for running simulations
        if status.is_running:
            time.sleep(5)
            st.rerun()
    
    elif status.exit_code is not None:
        st.markdown("---")
        
        # Error details
        if status.error_message:
            with st.expander("Error Details", expanded=True):
                st.error(status.error_message)
        
        # Log summary
        if status.log_lines:
            st.markdown("**Recent Log Output:**")
            log_text = "\n".join(status.log_lines[-20:])  # Show last 20 lines
            st.text_area("Logs", log_text, height=200, disabled=True)
    
    # Control buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if status.is_running:
            if st.button("⏸️ Pause Simulation", type="secondary"):
                st.info("Pause functionality not yet implemented")
        else:
            st.button("⏸️ Pause", type="secondary", disabled=True)
    
    with col2:
        if status.is_running:
            if st.button("⏹️ Stop Simulation", type="secondary"):
                st.info("Stop functionality not yet implemented")
        else:
            st.button("⏹️ Stop", type="secondary", disabled=True)
    
    with col3:
        if status.is_running:
            if st.button("📊 View Logs", type="secondary"):
                st.info("Switch to Logs tab to view real-time logs")
        else:
            st.button("📊 View Logs", type="secondary", disabled=True)

# Mapping Tab
with tabs[1]:
    st.header("Mapping")
    st.write("Primary Map Editor - Configure sector to product mappings with enhanced product selection")
    
    # Check if bundle is loaded
    if phase1_bundle is None:
        st.error("❌ Failed to load inputs.json. Please check the file and restart the application.")
        st.stop()
    
    # Get current mapping and available data from Phase1Bundle
    sectors = list(phase1_bundle.lists.sectors)
    products = list(phase1_bundle.lists.products)
    
    # Get current mapping from primary_map
    current_mapping = {}
    for _, row in phase1_bundle.primary_map.long.iterrows():
        sector = str(row["Sector"])
        product = str(row["Material"])
        start_year = float(row["StartYear"])
        
        if sector not in current_mapping:
            current_mapping[sector] = []
        
        current_mapping[sector].append({
            'product': product,
            'start_year': start_year
        })
    
    # Mode-aware mapping display
    current_mode = ui_state.runspecs.anchor_mode
    mode_desc = "Sector+Product specific parameters" if current_mode == 'sm' else 'Sector-level parameters'
    st.info(f"🎯 **Current Mode**: {current_mode.upper()} - {mode_desc}")
    
    # Enhanced mapping editor
    st.subheader("Enhanced Sector-Product Mapping Editor")
    
    # Sector selection
    selected_sector = st.selectbox(
        "Select Sector to Edit",
        options=sectors,
        key="mapping_sector_select"
    )
    
    if selected_sector:
        # Current mapping display
        st.subheader(f"Current Mapping for {selected_sector}")
        
        if selected_sector in current_mapping:
            current_entries = current_mapping[selected_sector]
            if current_entries:
                # Display current mapping in a nice table
                current_data = []
                for entry in current_entries:
                    current_data.append({
                        "Product": entry.get('product', 'Unknown'),
                        "Start Year": entry.get('start_year', 0.0),
                        "Status": "✅ Active" if entry.get('start_year', 0) > 0 else "⏸️ Disabled"
                    })
                
                st.dataframe(current_data, use_container_width=True)
            else:
                st.info("No products currently mapped to this sector")
        else:
            st.info("No products currently mapped to this sector")
        
        # Enhanced product selection with pillbox-style UI
        st.subheader("Product Selection & Configuration")
        
        # Product selection with search and filtering
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Product search/filter
            product_filter = st.text_input(
                "🔍 Filter Products",
                placeholder="Type to filter products...",
                key=f"product_filter_{selected_sector}"
            )
            
            # Filter products based on search
            filtered_products = products
            if product_filter:
                filtered_products = [p for p in products if product_filter.lower() in p.lower()]
        
        with col2:
            st.metric("Available Products", len(filtered_products))
        
        # Product selection with pillbox-style display
        st.write("**Select Products for this Sector:**")
        
        # Create a grid layout for product selection
        cols_per_row = 3
        selected_products = []
        
        # Get current selection from state
        current_selection = []
        if hasattr(ui_state, 'primary_map') and hasattr(ui_state.primary_map, 'by_sector'):
            if selected_sector in ui_state.primary_map.by_sector:
                current_selection = [e.product for e in ui_state.primary_map.by_sector[selected_sector]]
        
        # Display products in a grid with selection
        for i in range(0, len(filtered_products), cols_per_row):
            row_products = filtered_products[i:i + cols_per_row]
            cols = st.columns(len(row_products))
            
            for j, product in enumerate(row_products):
                with cols[j]:
                    # Create a pillbox-style selection
                    is_selected = product in current_selection
                    
                    # Product selection button
                    if st.button(
                        f"{'✅' if is_selected else '⭕'} {product}",
                        key=f"product_select_{selected_sector}_{product}",
                        type="primary" if is_selected else "secondary",
                        use_container_width=True
                    ):
                        # Toggle selection
                        if product in current_selection:
                            current_selection.remove(product)
                        else:
                            current_selection.append(product)
                        
                        # Update state
                        if not hasattr(ui_state, 'primary_map'):
                            ui_state.primary_map = PrimaryMapState()
                        
                        if selected_sector not in ui_state.primary_map.by_sector:
                            ui_state.primary_map.by_sector[selected_sector] = []
                        
                        # Update the mapping
                        if product in current_selection:
                            # Add product if not already present
                            if not any(e.product == product for e in ui_state.primary_map.by_sector[selected_sector]):
                                ui_state.primary_map.by_sector[selected_sector].append(
                                    PrimaryMapEntry(product=product, start_year=2025.0)
                                )
                        else:
                            # Remove product
                            ui_state.primary_map.by_sector[selected_sector] = [
                                e for e in ui_state.primary_map.by_sector[selected_sector] 
                                if e.product != product
                            ]
                        
                        # Update session state
                        st.session_state["ui_state"] = ui_state
                        st.rerun()
        
        # Product configuration table
        if current_selection:
            st.subheader("Product Configuration")
            st.write("Configure start years and parameters for selected products")
            
            # Create configuration table
            config_data = []
            updated_entries = []
            
            for product in current_selection:
                # Get current configuration
                current_start_year = 2025.0
                if hasattr(ui_state, 'primary_map') and selected_sector in ui_state.primary_map.by_sector:
                    for entry in ui_state.primary_map.by_sector[selected_sector]:
                        if entry.product == product:
                            current_start_year = entry.start_year
                            break
                
                # Product configuration row
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{product}**")
                
                with col2:
                    start_year = st.number_input(
                        "Start Year",
                        value=float(current_start_year),
                        min_value=0.0,
                        max_value=2100.0,
                        step=0.25,
                        format="%.2f",
                        key=f"start_year_{selected_sector}_{product}"
                    )
                
                with col3:
                    # Status indicator
                    if start_year > 0:
                        st.success("✅ Active")
                    else:
                        st.warning("⏸️ Disabled")
                
                # Store updated entry
                updated_entries.append(PrimaryMapEntry(product=product, start_year=start_year))
                
                # Add to display data
                config_data.append({
                    "Product": product,
                    "Start Year": start_year,
                    "Status": "Active" if start_year > 0 else "Disabled"
                })
            
            # Display configuration summary
            st.dataframe(config_data, use_container_width=True)
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("💾 Save Configuration", type="primary", use_container_width=True):
                    # Update state
                    if not hasattr(ui_state, 'primary_map'):
                        ui_state.primary_map = PrimaryMapState()
                    
                    ui_state.primary_map.by_sector[selected_sector] = updated_entries
                    
                    # Update session state
                    st.session_state["ui_state"] = ui_state
                    st.success(f"✅ Configuration saved for {selected_sector}")
                    st.rerun()
            
            with col2:
                if st.button("🔄 Reset to Current", type="secondary", use_container_width=True):
                    # Reset to current mapping
                    if hasattr(ui_state, 'primary_map') and selected_sector in ui_state.primary_map.by_sector:
                        del ui_state.primary_map.by_sector[selected_sector]
                        st.session_state["ui_state"] = ui_state
                        st.info("🔄 Reset to current mapping")
                        st.rerun()
            
            with col3:
                if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
                    # Clear all selections
                    if hasattr(ui_state, 'primary_map') and selected_sector in ui_state.primary_map.by_sector:
                        del ui_state.primary_map.by_sector[selected_sector]
                        st.session_state["ui_state"] = ui_state
                        st.info("🗑️ Cleared all selections")
                        st.rerun()
        
        # Global mapping summary
        st.subheader("Global Mapping Summary")
        
        if hasattr(ui_state, 'primary_map') and ui_state.primary_map.by_sector:
            summary_data = []
            for sector, entries in ui_state.primary_map.by_sector.items():
                for entry in entries:
                    summary_data.append({
                        "Sector": sector,
                        "Product": entry.product,
                        "Start Year": entry.start_year,
                        "Status": "Active" if entry.start_year > 0 else "Disabled"
                    })
            
            if summary_data:
                st.dataframe(summary_data, use_container_width=True)
                
                # Export options
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("📊 Export Mapping", type="secondary", use_container_width=True):
                        st.info("Export functionality will be implemented in Phase 4")
                
                with col2:
                    if st.button("🔄 Validate Mapping", type="secondary", use_container_width=True):
                        st.info("Validation will be integrated with scenario validation in Phase 4")
            else:
                st.info("No mapping overrides configured yet")
        else:
            st.info("No mapping overrides configured yet")
    
    # Mapping statistics and insights
    st.markdown("---")
    st.subheader("Mapping Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_sectors = len(sectors)
        mapped_sectors = len([s for s in sectors if s in current_mapping and current_mapping[s]])
        st.metric("Sectors with Products", f"{mapped_sectors}/{total_sectors}")
    
    with col2:
        total_products = len(products)
        mapped_products = len(set([
            entry.get('product') for sector_entries in current_mapping.values() 
            for entry in sector_entries
        ]))
        st.metric("Products in Use", f"{mapped_products}/{total_products}")
    
    with col3:
        active_mappings = sum([
            len([e for e in entries if e.get('start_year', 0) > 0])
            for entries in current_mapping.values()
        ])
        st.metric("Active Mappings", active_mappings)
    
    # Mode-specific information
    if current_mode == "sm":
        st.info("🔧 **SM Mode**: You can configure per-(sector, product) parameters in the Parameters tab")
    else:
        st.info("🔧 **Sector Mode**: Parameters are configured at the sector level in the Parameters tab")

# Logs Tab
with tabs[2]:
    st.header("Logs")
    
    # Enhanced Log Controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        log_level = st.selectbox("Log Level", ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"], index=0)
        auto_refresh = st.checkbox("Auto refresh", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 1, 10, 2, disabled=not auto_refresh)
    
    with col2:
        filter_text = st.text_input("Filter logs", placeholder="Enter text to filter...")
        show_timestamps = st.checkbox("Show timestamps", value=True)
        max_lines = st.number_input("Max lines to display", min_value=100, max_value=5000, value=1000, step=100)
    
    with col3:
        if st.button("Clear Logs", type="secondary"):
            st.session_state.logs_cleared = True
            st.rerun()
        
        if st.button("Export Logs", type="primary"):
            st.session_state.export_logs = True
    
    # Log Export Functionality
    if st.session_state.get("export_logs", False):
        st.session_state.export_logs = False
        
        # Get all available logs
        all_logs = runner_manager.read_log_file(10000)  # Get more lines for export
        
        if all_logs:
            # Apply current filters
            filtered_logs = all_logs
            if filter_text:
                filtered_logs = [line for line in filtered_logs if filter_text.lower() in line.lower()]
            
            if log_level != "ALL":
                level_map = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
                min_level = level_map.get(log_level, 1)
                
                level_filtered = []
                for line in filtered_logs:
                    if any(level in line.upper() for level in ["ERROR", "WARNING", "INFO", "DEBUG"]):
                        line_level = 1  # Default to INFO
                        if "ERROR" in line.upper():
                            line_level = 3
                        elif "WARNING" in line.upper():
                            line_level = 2
                        elif "DEBUG" in line.upper():
                            line_level = 0
                        
                        if line_level >= min_level:
                            level_filtered.append(line)
                    else:
                        level_filtered.append(line)
                filtered_logs = level_filtered
            
            # Create export data
            export_text = "\n".join(filtered_logs)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            st.download_button(
                label="Download Filtered Logs",
                data=export_text,
                file_name=f"logs_filtered_{timestamp}.txt",
                mime="text/plain"
            )
    
    # Enhanced Log Display
    if status.is_running or status.log_lines:
        # Get log lines based on current status
        if status.is_running:
            log_lines = status.log_lines
        else:
            log_lines = runner_manager.read_log_file(max_lines)
        
        # Apply text filter
        if filter_text:
            log_lines = [line for line in log_lines if filter_text.lower() in line.lower()]
        
        # Apply log level filter
        if log_level != "ALL":
            level_map = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
            min_level = level_map.get(log_level, 1)
            
            level_filtered = []
            for line in log_lines:
                if any(level in line.upper() for level in ["ERROR", "WARNING", "INFO", "DEBUG"]):
                    line_level = 1  # Default to INFO
                    if "ERROR" in line.upper():
                        line_level = 3
                    elif "WARNING" in line.upper():
                        line_level = 2
                    elif "DEBUG" in line.upper():
                        line_level = 0
                    
                    if line_level >= min_level:
                        level_filtered.append(line)
                else:
                    level_filtered.append(line)
            
            log_lines = level_filtered
        
        # Log Statistics
        if log_lines:
            st.subheader("Log Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Lines", len(log_lines))
            
            with col2:
                error_count = len([line for line in log_lines if "ERROR" in line.upper()])
                st.metric("Errors", error_count, delta=f"{error_count} found")
            
            with col3:
                warning_count = len([line for line in log_lines if "WARNING" in line.upper()])
                st.metric("Warnings", warning_count, delta=f"{warning_count} found")
            
            with col4:
                info_count = len([line for line in log_lines if "INFO" in line.upper()])
                st.metric("Info", info_count, delta=f"{info_count} found")
        
        # Enhanced Log Display with Syntax Highlighting
        st.subheader("Log Output")
        
        # Create a more sophisticated log display
        if log_lines:
            # Color-code log levels
            colored_logs = []
            for line in log_lines[-max_lines:]:  # Show last max_lines
                if "ERROR" in line.upper():
                    colored_logs.append(f"🔴 {line}")
                elif "WARNING" in line.upper():
                    colored_logs.append(f"🟡 {line}")
                elif "INFO" in line.upper():
                    colored_logs.append(f"🔵 {line}")
                elif "DEBUG" in line.upper():
                    colored_logs.append(f"⚪ {line}")
                else:
                    colored_logs.append(f"⚫ {line}")
            
            log_text = "\n".join(colored_logs)
            
            # Use text_area with better formatting
            st.text_area(
                "Live Log Stream", 
                log_text, 
                height=500,
                help="Logs are color-coded: 🔴 Error, 🟡 Warning, 🔵 Info, ⚪ Debug, ⚫ Other"
            )
            
            # Log navigation
            if len(log_lines) > max_lines:
                st.info(f"Showing last {max_lines} lines. Use export to see all logs.")
        else:
            st.info("No logs match the current filters.")
        
        # Auto-refresh functionality
        if auto_refresh and status.is_running:
            time.sleep(refresh_interval)
            st.rerun()
    else:
        st.info("No logs available. Start a simulation to see logs.")
        
        # Show log file status
        log_file_path = runner_manager.project_root / "logs" / "run.log"
        if log_file_path.exists():
            st.info(f"Log file exists at: {log_file_path}")
            try:
                with open(log_file_path, 'r') as f:
                    lines = f.readlines()
                    st.info(f"Log file contains {len(lines)} lines")
            except Exception as e:
                st.warning(f"Could not read log file: {e}")
        else:
            st.warning("No log file found. Logs will appear here when simulation starts.")

# Output Tab
with tabs[3]:
    st.header("Output")
    
    # Scenario Metadata Display
    st.subheader("Scenario Metadata")
    
    # Display current scenario information
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Current scenario details
        if hasattr(ui_state, 'runspecs') and ui_state.runspecs:
            st.info(f"**Current Configuration:** {ui_state.runspecs.anchor_mode.upper()} Mode")
            
            # Parameter summary
            param_summary = {
                "Anchor Mode": ui_state.runspecs.anchor_mode,
                "Total Sectors": len(phase1_bundle.lists.sectors) if phase1_bundle else 0,
                "Total Products": len(phase1_bundle.lists.products) if phase1_bundle else 0,
                "Points Overrides": len(ui_state.overrides.points),
                "Constants Overrides": len(ui_state.overrides.constants),
                "Seeds Configured": len(ui_state.seeds.active_anchor_clients) + len(ui_state.seeds.direct_clients)
            }
            
            for key, value in param_summary.items():
                st.metric(key, value)
    
    with col2:
        # Validation status
        st.subheader("Validation Status")
        
        # Check various validation states
        validation_checks = []
        
        # Check if bundle is loaded
        if phase1_bundle:
            validation_checks.append(("✅ Data Bundle", "Loaded successfully"))
        else:
            validation_checks.append(("❌ Data Bundle", "Failed to load"))
        
        # Check if sectors and products are available
        if phase1_bundle and hasattr(phase1_bundle, 'lists'):
            if phase1_bundle.lists.sectors:
                validation_checks.append(("✅ Sectors", f"{len(phase1_bundle.lists.sectors)} available"))
            else:
                validation_checks.append(("❌ Sectors", "No sectors found"))
            
            if phase1_bundle.lists.products:
                validation_checks.append(("✅ Products", f"{len(phase1_bundle.lists.products)} available"))
            else:
                validation_checks.append(("❌ Products", "No products found"))
        
        # Display validation status
        for status, message in validation_checks:
            st.write(f"{status}: {message}")
    
    st.markdown("---")
    
    # Enhanced Results Section
    st.subheader("Results")
    results_path = runner_manager.get_latest_results()
    
    if results_path and results_path.exists():
        try:
            df = pd.read_csv(results_path)
            st.success(f"Results loaded from: {results_path.name}")
            
            # Results Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                st.metric("File Size", f"{results_path.stat().st_size / 1024:.1f} KB")
            with col4:
                st.metric("Last Modified", time.strftime("%Y-%m-%d %H:%M", time.localtime(results_path.stat().st_mtime)))
            
            # Enhanced Data Display with Filtering
            st.subheader("Data Preview & Filtering")
            
            # Filtering options
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Column filter
                if df.columns.tolist():
                    selected_columns = st.multiselect(
                        "Select columns to display",
                        df.columns.tolist(),
                        default=df.columns.tolist()[:min(10, len(df.columns))]  # Default to first 10 columns
                    )
                else:
                    selected_columns = []
            
            with col2:
                # Row filter
                max_rows = st.number_input("Max rows to display", min_value=10, max_value=len(df), value=min(50, len(df)), step=10)
            
            # Apply filters
            if selected_columns:
                filtered_df = df[selected_columns].head(max_rows)
            else:
                filtered_df = df.head(max_rows)
            
            # Display filtered data
            st.dataframe(filtered_df, use_container_width=True)
            
            # Data summary
            if not filtered_df.empty:
                st.subheader("Data Summary")
                
                # Numeric columns summary
                numeric_cols = filtered_df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    st.write("**Numeric Columns Statistics:**")
                    summary_stats = filtered_df[numeric_cols].describe()
                    st.dataframe(summary_stats, use_container_width=True)
                
                # Categorical columns summary
                categorical_cols = filtered_df.select_dtypes(include=['object']).columns
                if len(categorical_cols) > 0:
                    st.write("**Categorical Columns Summary:**")
                    for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
                        value_counts = filtered_df[col].value_counts().head(10)
                        st.write(f"**{col}:**")
                        st.bar_chart(value_counts)
            
        except Exception as e:
            st.error(f"Error loading results: {e}")
            st.exception(e)
    else:
        st.info("No results available. Run a simulation to see results.")
    
    st.markdown("---")
    
    # Enhanced Export Section
    st.subheader("Export")
    
    if results_path and results_path.exists():
        try:
            df = pd.read_csv(results_path)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                export_format = st.selectbox("Export format", ["CSV", "Excel", "JSON", "Parquet"])
                
                # Export options
                include_index = st.checkbox("Include index", value=False)
                
                # Column selection for export
                export_columns = st.multiselect(
                    "Select columns to export",
                    df.columns.tolist(),
                    default=df.columns.tolist()
                )
            
            with col2:
                # Export filename
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                default_filename = f"results_{timestamp}"
                export_filename = st.text_input("Export filename", value=default_filename)
                
                # Export button
                if st.button("Export Results", type="primary"):
                    if export_columns:
                        export_df = df[export_columns]
                    else:
                        export_df = df
                    
                    try:
                        if export_format == "CSV":
                            csv_data = export_df.to_csv(index=include_index)
                            st.download_button(
                                label="Download CSV",
                                data=csv_data,
                                file_name=f"{export_filename}.csv",
                                mime="text/csv"
                            )
                        elif export_format == "Excel":
                            # Check if openpyxl is available
                            try:
                                import openpyxl
                                # Create Excel file in memory
                                output = io.BytesIO()
                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                    export_df.to_excel(writer, index=include_index, sheet_name='Results')
                                excel_data = output.getvalue()
                                
                                st.download_button(
                                    label="Download Excel",
                                    data=excel_data,
                                    file_name=f"{export_filename}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            except ImportError:
                                st.error("Excel export requires openpyxl package. Install with: pip install openpyxl")
                        elif export_format == "JSON":
                            json_data = export_df.to_json(orient="records", indent=2)
                            st.download_button(
                                label="Download JSON",
                                data=json_data,
                                file_name=f"{export_filename}.json",
                                mime="application/json"
                            )
                        elif export_format == "Parquet":
                            parquet_data = export_df.to_parquet(index=include_index)
                            st.download_button(
                                label="Download Parquet",
                                data=parquet_data,
                                file_name=f"{export_filename}.parquet",
                                mime="application/octet-stream"
                            )
                        
                        st.success("Export prepared successfully!")
                        
                    except Exception as e:
                        st.error(f"Export failed: {e}")
        except Exception as e:
            st.error(f"Error preparing export: {e}")
    else:
        st.info("No results available for export.")
    
    st.markdown("---")
    
    # Enhanced Plots Section
    st.subheader("Plots")
    plot_files = runner_manager.get_latest_plots()
    
    if plot_files:
        st.success(f"Found {len(plot_files)} plot files")
        
        # Plot filtering and organization
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Plot type filter
            plot_types = list(set([plot_path.stem.split('_')[0] if '_' in plot_path.stem else 'other' for plot_path in plot_files]))
            selected_plot_type = st.selectbox("Filter by plot type", ["All"] + plot_types)
            
            # Apply filter
            if selected_plot_type != "All":
                filtered_plots = [p for p in plot_files if p.stem.startswith(selected_plot_type)]
            else:
                filtered_plots = plot_files
        
        with col2:
            # Plot display options
            plots_per_row = st.selectbox("Plots per row", [1, 2, 3], index=1)
            show_captions = st.checkbox("Show captions", value=True)
        
        # Display plots in organized grid
        if filtered_plots:
            st.write(f"**Displaying {len(filtered_plots)} plots:**")
            
            # Create dynamic columns based on plots_per_row
            cols = st.columns(plots_per_row)
            
            for i, plot_path in enumerate(filtered_plots):
                col_idx = i % plots_per_row
                
                with cols[col_idx]:
                    # Display plot
                    st.image(str(plot_path), use_container_width=True)
                    
                    if show_captions:
                        st.caption(plot_path.name)
                    
                    # Download button
                    with open(plot_path, "rb") as f:
                        st.download_button(
                            label=f"Download {plot_path.name}",
                            data=f.read(),
                            file_name=plot_path.name,
                            mime="image/png"
                        )
                    
                    # Plot metadata
                    try:
                        file_size = plot_path.stat().st_size / 1024
                        modified_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(plot_path.stat().st_mtime))
                        st.caption(f"Size: {file_size:.1f} KB | Modified: {modified_time}")
                    except Exception:
                        pass
        else:
            st.info(f"No plots match the selected filter: {selected_plot_type}")
    else:
        st.info("No plots available. Run a simulation with visualization enabled to generate plots.")
        
        # Show plots directory status
        plots_dir = runner_manager.project_root / "output" / "plots"
        if plots_dir.exists():
            st.info(f"Plots directory exists at: {plots_dir}")
            try:
                plot_files_count = len(list(plots_dir.glob("*.png")))
                st.info(f"Plots directory contains {plot_files_count} PNG files")
            except Exception as e:
                st.warning(f"Could not read plots directory: {e}")
        else:
            st.warning("No plots directory found. Plots will appear here when simulation runs with visualization enabled.")

# Parameters Tab
with tabs[4]:
    st.header("Parameters")
    st.write("Enhanced Constants Editor - Configure model parameters with tabular input")
    
    # Check if bundle is loaded
    if phase1_bundle is None:
        st.error("❌ Failed to load inputs.json. Please check the file and restart the application.")
        st.stop()
    
    # Get current mode and mapping information
    current_mode = ui_state.runspecs.anchor_mode
    sectors = list(phase1_bundle.lists.sectors)
    products = list(phase1_bundle.lists.products)
    
    # Get current mapping from primary_map
    current_mapping = {}
    for _, row in phase1_bundle.primary_map.long.iterrows():
        sector = str(row["Sector"])
        product = str(row["Material"])
        start_year = float(row["StartYear"])
        
        if sector not in current_mapping:
            current_mapping[sector] = []
        
        current_mapping[sector].append({
            'product': product,
            'start_year': start_year
        })
    
    # Mode-specific parameter display
    mode_desc = "Sector+Product specific parameters" if current_mode == 'sm' else 'Sector-level parameters'
    st.info(f"🎯 **Current Mode**: {current_mode.upper()} - {mode_desc}")
    
    # Get permissible keys using the existing system
    try:
        permissible_keys = list_permissible_override_keys(phase1_bundle, anchor_mode=current_mode)
    except Exception as e:
        st.error(f"❌ Failed to get permissible keys: {e}")
        st.stop()
    
    # Enhanced parameter editor with tabular input
    st.subheader("Parameter Configuration")
    
    # Parameter type selection
    param_types = ["Anchor Parameters", "Other Parameters"]
    if current_mode == "sm":
        param_types.append("SM Mode Parameters")
    
    selected_param_type = st.selectbox(
        "Parameter Type",
        options=param_types,
        key="param_type_select"
    )
    
    if selected_param_type == "Anchor Parameters":
        st.subheader("Anchor Client Parameters (Per Sector)")
        
        # Get anchor parameters from Phase1Bundle
        anchor_params = phase1_bundle.anchor.by_sector
        
        if anchor_params is not None and not anchor_params.empty:
            # Create tabular input for anchor parameters
            st.write("Configure anchor client parameters for each sector")
            
            # Parameter categories
            param_categories = {
                "Timing": ["anchor_start_year", "anchor_client_activation_delay"],
                "Lead Generation": ["anchor_lead_generation_rate", "lead_to_pc_conversion_rate", "ATAM"],
                "Project Lifecycle": ["project_generation_rate", "max_projects_per_pc", "project_duration", "projects_to_client_conversion"],
                "Requirement Phases": ["initial_phase_duration", "ramp_phase_duration", "initial_requirement_rate", "initial_req_growth", "ramp_requirement_rate", "ramp_req_growth", "steady_requirement_rate", "steady_req_growth"],
                "Order Processing": ["requirement_to_order_lag"]
            }
            
            # Create tabs for each category
            category_tabs = st.tabs(list(param_categories.keys()))
            
            for i, (category, params) in enumerate(param_categories.items()):
                with category_tabs[i]:
                    st.write(f"**{category} Parameters**")
                    
                    # Create parameter table
                    param_data = []
                    updated_constants = {}
                    
                    for param in params:
                        if param in anchor_params.index:
                            # Get current values for each sector
                            row_data = {"Parameter": param}
                            
                            for sector in sectors:
                                # Get value from the anchor params DataFrame
                                current_value = anchor_params.loc[param, sector] if sector in anchor_params.columns else 0.0
                                
                                # Create input field
                                new_value = st.number_input(
                                    f"{param} ({sector})",
                                    value=float(current_value),
                                    step=0.01,
                                    format="%.2f",
                                    key=f"anchor_{param}_{sector}",
                                    help=f"Current value: {current_value}"
                                )
                                
                                row_data[sector] = new_value
                                
                                # Store updated value
                                param_key = f"{param}_{sector}"
                                if param_key in permissible_keys["constants"]:
                                    updated_constants[param_key] = new_value
                            
                            param_data.append(row_data)
                    
                    # Display parameter table
                    if param_data:
                        st.dataframe(param_data, use_container_width=True)
                        
                        # Save button for this category
                        if st.button(f"💾 Save {category} Parameters", type="primary", key=f"save_{category}"):
                            # Update state
                            if not hasattr(ui_state, 'overrides'):
                                ui_state.overrides = ScenarioOverridesState()
                            
                            ui_state.overrides.constants.update(updated_constants)
                            
                            # Update session state
                            st.session_state["ui_state"] = ui_state
                            st.success(f"✅ {category} parameters saved successfully!")
                            st.rerun()
        
        else:
            st.warning("No anchor parameters found in the data")
    
    elif selected_param_type == "Other Parameters":
        st.subheader("Other Client Parameters (Per Product)")
        
        # Get other parameters from Phase1Bundle
        other_params = phase1_bundle.other.by_product
        
        if other_params is not None and not other_params.empty:
            # Create tabular input for other parameters
            st.write("Configure other client parameters for each product")
            
            # Parameter categories
            param_categories = {
                "Timing": ["lead_start_year"],
                "Lead Generation": ["inbound_lead_generation_rate", "outbound_lead_generation_rate", "TAM"],
                "Conversion": ["lead_to_c_conversion_rate"],
                "Delays": ["lead_to_requirement_delay", "requirement_to_fulfilment_delay"],
                "Order Behavior": ["avg_order_quantity_initial", "client_requirement_growth"]
            }
            
            # Create tabs for each category
            category_tabs = st.tabs(list(param_categories.keys()))
            
            for i, (category, params) in enumerate(param_categories.items()):
                with category_tabs[i]:
                    st.write(f"**{category} Parameters**")
                    
                    # Create parameter table
                    param_data = []
                    updated_constants = {}
                    
                    for param in params:
                        if param in other_params.index:
                            # Get current values for each product
                            row_data = {"Parameter": param}
                            
                            for product in products:
                                # Get value from the other params DataFrame
                                current_value = other_params.loc[param, product] if product in other_params.columns else 0.0
                                
                                # Create input field
                                new_value = st.number_input(
                                    f"{param} ({product})",
                                    value=float(current_value),
                                    step=0.01,
                                    format="%.2f",
                                    key=f"other_{param}_{product}",
                                    help=f"Current value: {current_value}"
                                )
                                
                                row_data[product] = new_value
                                
                                # Store updated value
                                param_key = f"{param}_{product}"
                                if param_key in permissible_keys["constants"]:
                                    updated_constants[param_key] = new_value
                            
                            param_data.append(row_data)
                    
                    # Display parameter table
                    if param_data:
                        st.dataframe(param_data, use_container_width=True)
                        
                        # Save button for this category
                        if st.button(f"💾 Save {category} Parameters", type="primary", key=f"save_other_{category}"):
                            # Update state
                            if not hasattr(ui_state, 'overrides'):
                                ui_state.overrides = ScenarioOverridesState()
                            
                            ui_state.overrides.constants.update(updated_constants)
                            
                            # Update session state
                            st.session_state["ui_state"] = ui_state
                            st.success(f"✅ {category} parameters saved successfully!")
                            st.rerun()
        
        else:
            st.warning("No other parameters found in the data")
    
    elif selected_param_type == "SM Mode Parameters" and current_mode == "sm":
        st.subheader("SM Mode Parameters (Per Sector+Product)")
        
        # Get SM parameters from Phase1Bundle
        sm_params = phase1_bundle.anchor_sm
        
        if sm_params is not None and not sm_params.empty:
            # Create tabular input for SM parameters
            st.write("Configure SM mode parameters for each sector-product pair")
            
            # Get current mapping to determine which pairs to show
            active_pairs = []
            for sector, entries in current_mapping.items():
                for entry in entries:
                    if entry.get('start_year', 0) > 0:  # Only active mappings
                        active_pairs.append((sector, entry['product']))
            
            if active_pairs:
                # Parameter categories for SM mode
                param_categories = {
                    "Timing": ["anchor_start_year", "anchor_client_activation_delay"],
                    "Lead Generation": ["anchor_lead_generation_rate", "lead_to_pc_conversion_rate", "ATAM"],
                    "Project Lifecycle": ["project_generation_rate", "max_projects_per_pc", "project_duration", "projects_to_client_conversion"],
                    "Requirement Phases": ["initial_phase_duration", "ramp_phase_duration", "initial_requirement_rate", "initial_req_growth", "ramp_requirement_rate", "ramp_req_growth", "steady_requirement_rate", "steady_req_growth"],
                    "Order Processing": ["requirement_to_order_lag"]
                }
                
                # Create tabs for each category
                category_tabs = st.tabs(list(param_categories.keys()))
                
                for i, (category, params) in enumerate(param_categories.items()):
                    with category_tabs[i]:
                        st.write(f"**{category} Parameters**")
                        
                        # Create parameter table
                        param_data = []
                        updated_constants = {}
                        
                        for param in params:
                            # Filter SM params for this parameter
                            param_rows = sm_params[sm_params["Param"] == param]
                            
                            if not param_rows.empty:
                                # Get current values for each sector-product pair
                                row_data = {"Parameter": param}
                                
                                for sector, product in active_pairs:
                                    # Find the value for this sector-product pair
                                    pair_row = param_rows[
                                        (param_rows["Sector"] == sector) & 
                                        (param_rows["Material"] == product)
                                    ]
                                    
                                    if not pair_row.empty:
                                        current_value = float(pair_row.iloc[0]["Value"])
                                    else:
                                        current_value = 0.0
                                    
                                    # Create input field
                                    new_value = st.number_input(
                                        f"{param} ({sector}-{product})",
                                        value=float(current_value),
                                        step=0.01,
                                        format="%.2f",
                                        key=f"sm_{param}_{sector}_{product}",
                                        help=f"Current value: {current_value}"
                                    )
                                    
                                    row_data[f"{sector}-{product}"] = new_value
                                    
                                    # Store updated value
                                    param_key = f"{param}_{sector}_{product}"
                                    if param_key in permissible_keys["constants"]:
                                        updated_constants[param_key] = new_value
                                
                                param_data.append(row_data)
                        
                        # Display parameter table
                        if param_data:
                            st.dataframe(param_data, use_container_width=True)
                            
                            # Save button for this category
                            if st.button(f"💾 Save {category} Parameters", type="primary", key=f"save_sm_{category}"):
                                # Update state
                                if not hasattr(ui_state, 'overrides'):
                                    ui_state.overrides = ScenarioOverridesState()
                                
                                ui_state.overrides.constants.update(updated_constants)
                                
                                # Update session state
                                st.session_state["ui_state"] = ui_state
                                st.success(f"✅ {category} parameters saved successfully!")
                                st.rerun()
            else:
                st.info("No active sector-product mappings found. Configure mappings in the Mapping tab first.")
        
        else:
            st.warning("No SM mode parameters found in the data")
    
    # Parameter summary and validation
    st.markdown("---")
    st.subheader("Parameter Summary & Validation")
    
    # Show current overrides
    if hasattr(ui_state, 'overrides') and ui_state.overrides.constants:
        st.write("**Current Parameter Overrides:**")
        
        # Group by parameter type
        override_data = []
        for key, value in ui_state.overrides.constants.items():
            if "_" in key:
                parts = key.split("_")
                if len(parts) >= 2:
                    param_type = parts[0]
                    if len(parts) >= 3:
                        entity = parts[1]
                        if len(parts) >= 4:
                            sub_entity = parts[2]
                            override_data.append({
                                "Parameter": "_".join(parts[:-2]),
                                "Entity": f"{entity}_{sub_entity}",
                                "Value": value,
                                "Type": "Override"
                            })
                        else:
                            override_data.append({
                                "Parameter": "_".join(parts[:-1]),
                                "Entity": entity,
                                "Value": value,
                                "Type": "Override"
                            })
                    else:
                        override_data.append({
                            "Parameter": key,
                            "Entity": "Unknown",
                            "Value": value,
                            "Type": "Override"
                        })
                else:
                    override_data.append({
                        "Parameter": key,
                        "Entity": "Unknown",
                        "Value": value,
                        "Type": "Override"
                    })
        
        if override_data:
            st.dataframe(override_data, use_container_width=True)
            
            # Validation and export options
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔍 Validate Parameters", type="secondary", use_container_width=True):
                    st.info("Parameter validation will be integrated with scenario validation")
            
            with col2:
                if st.button("📊 Export Parameters", type="secondary", use_container_width=True):
                    st.info("Export functionality will be implemented in Phase 4")
        else:
            st.info("No parameter overrides configured yet")
    else:
        st.info("No parameter overrides configured yet")
    
    # Parameter statistics
    st.markdown("---")
    st.subheader("Parameter Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_params = len(permissible_keys["constants"])
        configured_params = len(ui_state.overrides.constants) if hasattr(ui_state, 'overrides') else 0
        st.metric("Parameters Configured", f"{configured_params}/{total_params}")
    
    with col2:
        if hasattr(ui_state, 'overrides') and ui_state.overrides.constants:
            override_count = len(ui_state.overrides.constants)
            st.metric("Active Overrides", override_count)
        else:
            st.metric("Active Overrides", 0)
    
    with col3:
        if hasattr(ui_state, 'overrides') and ui_state.overrides.constants:
            # Calculate percentage of parameters with overrides
            override_percentage = (len(ui_state.overrides.constants) / len(permissible_keys["constants"])) * 100
            st.metric("Override Coverage", f"{override_percentage:.1f}%")
        else:
            st.metric("Override Coverage", "0%")

# Points Tab
with tabs[5]:
    st.header("Points")
    st.write("Points Editor - Configure time-series data")
    
    # Get permissible keys
    permissible_keys = data_manager.get_permissible_keys(ui_state.runspecs.anchor_mode)
    
    # Import the updated points editor
    from ui.components.points_editor import render_points_editor, render_points_summary
    
    # Points editor with real-time updates
    def update_points(new_points):
        """Update points in the state manager."""
        state_manager.update_overrides(points=new_points)
        st.session_state["ui_state"] = state_manager.get_state()
    
    updated_points = render_points_editor(
        state=ui_state.overrides,
        permissible_points=permissible_keys.points,
        on_points_update=update_points
    )
    
    # Show points summary
    st.markdown("---")
    render_points_summary(updated_points.points)

# Seeds Tab
with tabs[6]:
    st.header("Seeds")
    st.write("Enhanced Seeds Editor - Configure initial conditions with comprehensive table format")
    
    # Check if bundle is loaded
    if phase1_bundle is None:
        st.error("❌ Failed to load inputs.json. Please check the file and restart the application.")
        st.stop()
    
    # Get current mode and available data
    current_mode = ui_state.runspecs.anchor_mode
    sectors = list(phase1_bundle.lists.sectors)
    products = list(phase1_bundle.lists.products)
    
    # Mode-aware seeds display
    st.info(f"🎯 **Current Mode**: {current_mode.upper()} - {'Sector+Product specific seeding' if current_mode == 'sm' else 'Sector-level seeding'}")
    
    # Enhanced seeds editor
    st.subheader("Initial Conditions Configuration")
    
    # Create tabs for different seed types
    seed_tabs = st.tabs([
        "Active Anchor Clients", 
        "Direct Clients", 
        "Completed Projects",
        "Elapsed Quarters"
    ])
    
    # Tab 1: Active Anchor Clients
    with seed_tabs[0]:
        st.write("Configure active anchor clients at t0")
        
        if current_mode == "sector":
            st.subheader("Sector Mode - Active Anchor Clients")
            
            # Create table for sector-level seeds
            sector_seeds_data = []
            updated_sector_seeds = {}
            
            for sector in sectors:
                current_count = ui_state.seeds.active_anchor_clients.get(sector, 0)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{sector}**")
                
                with col2:
                    seed_count = st.number_input(
                        "Active Clients",
                        value=int(current_count),
                        min_value=0,
                        step=1,
                        key=f"sector_seed_{sector}"
                    )
                
                with col3:
                    if seed_count > 0:
                        st.success(f"✅ {seed_count} active")
                    else:
                        st.info("⏸️ No seeds")
                
                # Store updated value
                updated_sector_seeds[sector] = seed_count
                sector_seeds_data.append({
                    "Sector": sector,
                    "Active Clients": seed_count,
                    "Status": "Active" if seed_count > 0 else "No Seeds"
                })
            
            # Display sector seeds table
            st.dataframe(sector_seeds_data, use_container_width=True)
            
            # Save button for sector seeds
            if st.button("💾 Save Sector Seeds", type="primary", key="save_sector_seeds"):
                ui_state.seeds.active_anchor_clients = updated_sector_seeds
                st.session_state["ui_state"] = ui_state
                st.success("✅ Sector seeds saved successfully!")
                st.rerun()
        
        else:
            st.subheader("SM Mode - Active Anchor Clients")
            
            # Create table for SM mode seeds
            sm_seeds_data = []
            updated_sm_seeds = {}
            
            # Get current mapping to determine which pairs to show
            current_mapping = {}
            for _, row in phase1_bundle.primary_map.long.iterrows():
                sector = str(row["Sector"])
                product = str(row["Material"])
                start_year = float(row["StartYear"])
                
                if sector not in current_mapping:
                    current_mapping[sector] = []
                
                current_mapping[sector].append({
                    'product': product,
                    'start_year': start_year
                })
            
            # Create SM seeds table
            for sector, entries in current_mapping.items():
                for entry in entries:
                    product = entry['product']
                    pair_key = f"{sector}_{product}"
                    
                    # Get current seed count
                    current_count = 0
                    if sector in ui_state.seeds.active_anchor_clients_sm:
                        current_count = ui_state.seeds.active_anchor_clients_sm[sector].get(product, 0)
                    
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**{sector}**")
                    
                    with col2:
                        st.write(f"**{product}**")
                    
                    with col3:
                        seed_count = st.number_input(
                            "Active Clients",
                            value=int(current_count),
                            min_value=0,
                            step=1,
                            key=f"sm_seed_{sector}_{product}"
                        )
                    
                    with col4:
                        if seed_count > 0:
                            st.success(f"✅ {seed_count} active")
                        else:
                            st.info("⏸️ No seeds")
                    
                    # Store updated value
                    if sector not in updated_sm_seeds:
                        updated_sm_seeds[sector] = {}
                    updated_sm_seeds[sector][product] = seed_count
                    
                    sm_seeds_data.append({
                        "Sector": sector,
                        "Product": product,
                        "Active Clients": seed_count,
                        "Status": "Active" if seed_count > 0 else "No Seeds"
                    })
            
            # Display SM seeds table
            if sm_seeds_data:
                st.dataframe(sm_seeds_data, use_container_width=True)
                
                # Save button for SM seeds
                if st.button("💾 Save SM Seeds", type="primary", key="save_sm_seeds"):
                    ui_state.seeds.active_anchor_clients_sm = updated_sm_seeds
                    st.session_state["ui_state"] = ui_state
                    st.success("✅ SM seeds saved successfully!")
                    st.rerun()
            else:
                st.info("No sector-product mappings found. Configure mappings in the Mapping tab first.")
    
    # Tab 2: Direct Clients
    with seed_tabs[1]:
        st.subheader("Direct Client Seeds")
        st.write("Configure direct clients per product at t0")
        
        # Create table for direct client seeds
        direct_seeds_data = []
        updated_direct_seeds = {}
        
        for product in products:
            current_count = ui_state.seeds.direct_clients.get(product, 0)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{product}**")
            
            with col2:
                seed_count = st.number_input(
                    "Direct Clients",
                    value=int(current_count),
                    min_value=0,
                    step=1,
                    key=f"direct_seed_{product}"
                )
            
            with col3:
                if seed_count > 0:
                    st.success(f"✅ {seed_count} clients")
                else:
                    st.info("⏸️ No seeds")
            
            # Store updated value
            updated_direct_seeds[product] = seed_count
            direct_seeds_data.append({
                "Product": product,
                "Direct Clients": seed_count,
                "Status": "Active" if seed_count > 0 else "No Seeds"
            })
        
        # Display direct seeds table
        st.dataframe(direct_seeds_data, use_container_width=True)
        
        # Save button for direct seeds
        if st.button("💾 Save Direct Client Seeds", type="primary", key="save_direct_seeds"):
            ui_state.seeds.direct_clients = updated_direct_seeds
            st.session_state["ui_state"] = ui_state
            st.success("✅ Direct client seeds saved successfully!")
            st.rerun()
    
    # Tab 3: Completed Projects
    with seed_tabs[2]:
        st.write("Configure completed projects backlog at t0")
        
        if current_mode == "sector":
            st.subheader("Sector Mode - Completed Projects")
            
            # Create table for sector-level completed projects
            completed_projects_data = []
            updated_completed_projects = {}
            
            for sector in sectors:
                current_count = ui_state.seeds.completed_projects.get(sector, 0)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{sector}**")
                
                with col2:
                    project_count = st.number_input(
                        "Completed Projects",
                        value=int(current_count),
                        min_value=0,
                        step=1,
                        key=f"completed_projects_{sector}"
                    )
                
                with col3:
                    if project_count > 0:
                        st.success(f"✅ {project_count} projects")
                    else:
                        st.info("⏸️ No backlog")
                
                # Store updated value
                updated_completed_projects[sector] = project_count
                completed_projects_data.append({
                    "Sector": sector,
                    "Completed Projects": project_count,
                    "Status": "Active" if project_count > 0 else "No Backlog"
                })
            
            # Display completed projects table
            st.dataframe(completed_projects_data, use_container_width=True)
            
            # Save button for completed projects
            if st.button("💾 Save Completed Projects", type="primary", key="save_completed_projects"):
                ui_state.seeds.completed_projects = updated_completed_projects
                st.session_state["ui_state"] = ui_state
                st.success("✅ Completed projects saved successfully!")
                st.rerun()
        
        else:
            st.subheader("SM Mode - Completed Projects")
            
            # Create table for SM mode completed projects
            sm_completed_data = []
            updated_sm_completed = {}
            
            # Use the same mapping logic as SM seeds
            current_mapping = {}
            for _, row in phase1_bundle.primary_map.long.iterrows():
                sector = str(row["Sector"])
                product = str(row["Material"])
                start_year = float(row["StartYear"])
                
                if sector not in current_mapping:
                    current_mapping[sector] = []
                
                current_mapping[sector].append({
                    'product': product,
                    'start_year': start_year
                })
            
            # Create SM completed projects table
            for sector, entries in current_mapping.items():
                for entry in entries:
                    product = entry['product']
                    
                    # Get current completed projects count
                    current_count = 0
                    if sector in ui_state.seeds.completed_projects_sm:
                        current_count = ui_state.seeds.completed_projects_sm[sector].get(product, 0)
                    
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**{sector}**")
                    
                    with col2:
                        st.write(f"**{product}**")
                    
                    with col3:
                        project_count = st.number_input(
                            "Completed Projects",
                            value=int(current_count),
                            min_value=0,
                            step=1,
                            key=f"sm_completed_{sector}_{product}"
                        )
                    
                    with col4:
                        if project_count > 0:
                            st.success(f"✅ {project_count} projects")
                        else:
                            st.info("⏸️ No backlog")
                    
                    # Store updated value
                    if sector not in updated_sm_completed:
                        updated_sm_completed[sector] = {}
                    updated_sm_completed[sector][product] = project_count
                    
                    sm_completed_data.append({
                        "Sector": sector,
                        "Product": product,
                        "Completed Projects": project_count,
                        "Status": "Active" if project_count > 0 else "No Backlog"
                    })
            
            # Display SM completed projects table
            if sm_completed_data:
                st.dataframe(sm_completed_data, use_container_width=True)
                
                # Save button for SM completed projects
                if st.button("💾 Save SM Completed Projects", type="primary", key="save_sm_completed"):
                    ui_state.seeds.completed_projects_sm = updated_sm_completed
                    st.session_state["ui_state"] = ui_state
                    st.success("✅ SM completed projects saved successfully!")
                    st.rerun()
            else:
                st.info("No sector-product mappings found. Configure mappings in the Mapping tab first.")
    
    # Tab 4: Elapsed Quarters
    with seed_tabs[3]:
        st.write("Configure aging for existing clients (optional)")
        
        if current_mode == "sector":
            st.subheader("Sector Mode - Elapsed Quarters")
            
            # Create table for sector-level elapsed quarters
            elapsed_quarters_data = []
            updated_elapsed_quarters = {}
            
            for sector in sectors:
                current_quarters = ui_state.seeds.elapsed_quarters.get(sector, 0)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{sector}**")
                
                with col2:
                    quarters = st.number_input(
                        "Elapsed Quarters",
                        value=int(current_quarters),
                        min_value=0,
                        step=1,
                        key=f"elapsed_quarters_{sector}"
                    )
                
                with col3:
                    if quarters > 0:
                        st.info(f"⏰ {quarters} quarters")
                    else:
                        st.info("🆕 No aging")
                
                # Store updated value
                updated_elapsed_quarters[sector] = quarters
                elapsed_quarters_data.append({
                    "Sector": sector,
                    "Elapsed Quarters": quarters,
                    "Status": "Aged" if quarters > 0 else "No Aging"
                })
            
            # Display elapsed quarters table
            st.dataframe(elapsed_quarters_data, use_container_width=True)
            
            # Save button for elapsed quarters
            if st.button("💾 Save Elapsed Quarters", type="primary", key="save_elapsed_quarters"):
                ui_state.seeds.elapsed_quarters = updated_elapsed_quarters
                st.session_state["ui_state"] = ui_state
                st.success("✅ Elapsed quarters saved successfully!")
                st.rerun()
        
        else:
            st.subheader("SM Mode - Elapsed Quarters")
            st.info("SM mode elapsed quarters functionality will be implemented in future phases")
    
    # Global seeds summary
    st.markdown("---")
    st.subheader("Global Seeds Summary")
    
    # Collect all seeds data for summary
    summary_data = []
    
    # Sector mode seeds
    if current_mode == "sector":
        for sector, count in ui_state.seeds.active_anchor_clients.items():
            if count > 0:
                summary_data.append({
                    "Type": "Active Anchor Clients",
                    "Entity": sector,
                    "Count": count,
                    "Mode": "Sector"
                })
        
        for sector, count in ui_state.seeds.completed_projects.items():
            if count > 0:
                summary_data.append({
                    "Type": "Completed Projects",
                    "Entity": sector,
                    "Count": count,
                    "Mode": "Sector"
                })
    
    # SM mode seeds
    else:
        for sector, products in ui_state.seeds.active_anchor_clients_sm.items():
            for product, count in products.items():
                if count > 0:
                    summary_data.append({
                        "Type": "Active Anchor Clients",
                        "Entity": f"{sector} - {product}",
                        "Count": count,
                        "Mode": "SM"
                    })
        
        for sector, products in ui_state.seeds.completed_projects_sm.items():
            for product, count in products.items():
                if count > 0:
                    summary_data.append({
                        "Type": "Completed Projects",
                        "Entity": f"{sector} - {product}",
                        "Count": count,
                        "Mode": "SM"
                    })
    
    # Direct client seeds
    for product, count in ui_state.seeds.direct_clients.items():
        if count > 0:
            summary_data.append({
                "Type": "Direct Clients",
                "Entity": product,
                "Count": count,
                "Mode": "Product"
            })
    
    # Elapsed quarters
    for sector, quarters in ui_state.seeds.elapsed_quarters.items():
        if quarters > 0:
            summary_data.append({
                "Type": "Elapsed Quarters",
                "Entity": sector,
                "Count": quarters,
                "Mode": "Sector"
            })
    
    # Display summary
    if summary_data:
        st.dataframe(summary_data, use_container_width=True)
        
        # Export and validation options
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📊 Export Seeds", type="secondary", use_container_width=True):
                st.info("Export functionality will be implemented in Phase 5")
        
        with col2:
            if st.button("🔄 Validate Seeds", type="secondary", use_container_width=True):
                st.info("Seed validation will be integrated with scenario validation")
    else:
        st.info("No seeds configured yet")
    
    # Seeds statistics
    st.markdown("---")
    st.subheader("Seeds Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_seeds = sum([
            sum(ui_state.seeds.active_anchor_clients.values()),
            sum(ui_state.seeds.direct_clients.values()),
            sum(ui_state.seeds.completed_projects.values())
        ])
        if current_mode == "sm":
            total_seeds += sum([
                sum(sum(products.values()) for products in ui_state.seeds.active_anchor_clients_sm.values()),
                sum(sum(products.values()) for products in ui_state.seeds.completed_projects_sm.values())
            ])
        st.metric("Total Seeds", total_seeds)
    
    with col2:
        active_sectors = len([s for s, c in ui_state.seeds.active_anchor_clients.items() if c > 0])
        if current_mode == "sm":
            active_sectors = len([s for s, products in ui_state.seeds.active_anchor_clients_sm.items() if any(c > 0 for c in products.values())])
        st.metric("Active Sectors", active_sectors)
    
    with col3:
        active_products = len([p for p, c in ui_state.seeds.direct_clients.items() if c > 0])
        st.metric("Active Products", active_products)
    
    # Mode-specific information
    if current_mode == "sm":
        st.info("🔧 **SM Mode**: Seeds are configured per (sector, product) pair based on current mappings")
    else:
        st.info("🔧 **Sector Mode**: Seeds are configured at the sector level for all products")

# Sidebar with additional controls
with st.sidebar:
    st.header("Application Controls")
    
    # Scenario name
    scenario_name = st.text_input("Scenario Name", value=ui_state.name)
    if scenario_name != ui_state.name:
        state_manager.update_state(name=scenario_name)
        st.session_state["ui_state"] = state_manager.get_state()
    
    # Runspecs
    st.subheader("Runspecs")
    start_time = st.number_input("Start Time", value=ui_state.runspecs.starttime, step=0.25)
    stop_time = st.number_input("Stop Time", value=ui_state.runspecs.stoptime, step=0.25)
    dt = st.number_input("Time Step (dt)", value=ui_state.runspecs.dt, step=0.25, min_value=0.01)
    anchor_mode = st.selectbox("Anchor Mode", ["sector", "sm"], index=0 if ui_state.runspecs.anchor_mode == "sector" else 1)
    
    # Update runspecs if changed
    if (start_time != ui_state.runspecs.starttime or stop_time != ui_state.runspecs.stoptime or 
        dt != ui_state.runspecs.dt or anchor_mode != ui_state.runspecs.anchor_mode):
        state_manager.update_runspecs(
            starttime=start_time,
            stoptime=stop_time,
            dt=dt,
            anchor_mode=anchor_mode
        )
        st.session_state["ui_state"] = state_manager.get_state()
    
    # Save scenario
    st.subheader("Save Scenario")
    save_name = st.text_input("Save as", value=ui_state.name)
    overwrite = st.checkbox("Overwrite existing", value=False)
    
    if st.button("Save Scenario"):
        success, error, path = scenario_manager.save_current_state_as_scenario(save_name, overwrite)
        if success:
            st.success(f"Scenario saved to {path}")
        else:
            st.error(f"Error saving scenario: {error}")
    
    # Validation
    st.subheader("Validation")
    if st.button("Validate Current Scenario"):
        permissible_keys = data_manager.get_permissible_keys(ui_state.runspecs.anchor_mode)
        validation_result = validation_manager.validate_current_state({
            'constants': permissible_keys.constants,
            'points': permissible_keys.points,
            'sectors': permissible_keys.sectors,
            'products': permissible_keys.products
        })
        
        if validation_result.is_valid:
            st.success("✅ Scenario is valid")
        else:
            st.error("❌ Scenario has validation errors:")
            for error in validation_result.errors[:5]:  # Show first 5 errors
                st.error(f"- {error.field}: {error.message}")
            if len(validation_result.errors) > 5:
                st.error(f"... and {len(validation_result.errors) - 5} more errors")
    
    # Data info
    st.subheader("Data Info")
    bundle = data_manager.get_data_bundle()
    if bundle:
        st.write(f"Sectors: {len(bundle.lists.get('sectors', []))}")
        st.write(f"Products: {len(bundle.lists.get('products', []))}")
    else:
        st.error("Data not loaded")

# Footer
st.markdown("---")
st.info(
    "✅ **Phase 2 Complete**: Enhanced Runner tab with comprehensive scenario management, "
    "run controls, mode toggle integration, and real-time validation feedback. "
    "Parameters and Points tabs now fully functional with updated components."
)
