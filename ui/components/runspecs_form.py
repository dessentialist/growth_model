from __future__ import annotations

"""
Enhanced Runspecs form component for Streamlit.

This module renders inputs for starttime, stoptime, dt, anchor_mode, and scenario management
with save protection and change tracking. It performs light, immediate validation to
ensure values are in sensible ranges before the backend validation.
"""

from typing import Tuple, Optional
import streamlit as st
from pathlib import Path

from ui.state import RunspecsState
from ui.services.builder import list_available_scenarios, read_scenario_yaml
from src.io_paths import SCENARIOS_DIR


def render_runspecs_form(
    state: RunspecsState, 
    bundle=None, 
    on_save_callback=None
) -> Tuple[RunspecsState, list[str]]:
    """Render the enhanced runspecs editor and return (updated_state, inline_errors).

    We run simple checks here: start < stop, dt > 0, anchor_mode in {sector, sm}.
    Backend will re-validate comprehensively on Save/Validate.
    
    Args:
        state: Current RunspecsState to edit
        bundle: Optional Phase1Bundle for scenario loading
        on_save_callback: Optional callback function when save is clicked
        
    Returns:
        Tuple of (updated_state, list_of_errors)
    """
    st.subheader("Runtime Controls")
    
    # Initialize session state for scenario tracking (persistent across reruns)
    if "loaded_scenario_name" not in st.session_state:
        st.session_state.loaded_scenario_name = "working_scenario"
    
    # Create a copy of the current state for editing
    editing_state = RunspecsState(
        starttime=state.starttime,
        stoptime=state.stoptime,
        dt=state.dt,
        anchor_mode=state.anchor_mode
    )
    
    # Track if changes were made
    changes_made = False
    
    # Runtime Controls Section
    st.markdown("**Time Configuration**")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    
    with c1:
        new_start = st.number_input(
            "Start Time (year)", 
            value=float(editing_state.starttime), 
            step=0.25, 
            format="%.2f",
            key="runspecs_start"
        )
        if new_start != editing_state.starttime:
            editing_state.starttime = new_start
            changes_made = True
    
    with c2:
        new_stop = st.number_input(
            "Stop Time (year)", 
            value=float(editing_state.stoptime), 
            step=0.25, 
            format="%.2f",
            key="runspecs_stop"
        )
        if new_stop != editing_state.stoptime:
            editing_state.stoptime = new_stop
            changes_made = True
    
    with c3:
        new_dt = st.number_input(
            "dt (years)", 
            value=float(editing_state.dt), 
            step=0.25, 
            format="%.2f", 
            min_value=0.01,
            key="runspecs_dt"
        )
        if new_dt != editing_state.dt:
            editing_state.dt = new_dt
            changes_made = True
    
    with c4:
        new_mode = st.selectbox(
            "Anchor Mode", 
            options=["sector", "sm"], 
            index=(0 if editing_state.anchor_mode == "sector" else 1),
            key="runspecs_mode"
        )
        if new_mode != editing_state.anchor_mode:
            editing_state.anchor_mode = new_mode
            changes_made = True
    
    # Anchor Mode Selection Section
    st.markdown("**Anchor Mode Configuration**")
    if editing_state.anchor_mode == "sector":
        st.info("🔧 **Sector Mode**: Anchor clients are created per sector with sector-level parameters.")
    else:
        st.info("🔧 **SM Mode**: Anchor clients are created per (sector, product) pair with per-pair parameters.")
    
    # Scenario Management Section
    st.markdown("**Scenario Management**")
    
    # Scenario Name Input - use session state for persistence
    scenario_name = st.text_input(
        "Scenario Name",
        value=st.session_state.loaded_scenario_name,
        placeholder="Enter scenario name",
        help="Name for the current scenario configuration",
        key="scenario_name_input"
    )
    
    # Check if user entered a different scenario name
    scenario_name_changed = scenario_name != st.session_state.loaded_scenario_name
    
    # Save New Scenario Button (only shown when scenario name changes)
    if scenario_name_changed:
        st.markdown("**🆕 Create New Scenario**")
        st.caption("You've entered a new scenario name. Click below to create and save this new scenario.")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("💾 Save New Scenario", type="primary", key="save_new_scenario_btn"):
                try:
                    # Create the new scenario file
                    from ui.services.builder import write_scenario_yaml
                    
                    # Build scenario data from current state
                    new_scenario_data = {
                        "name": scenario_name,
                        "runspecs": {
                            "starttime": editing_state.starttime,
                            "stoptime": editing_state.stoptime,
                            "dt": editing_state.dt,
                            "anchor_mode": editing_state.anchor_mode
                        },
                        "overrides": {
                            "constants": {},
                            "points": {},
                            "primary_map": {}
                        }
                    }
                    
                    # Save the new scenario
                    scenario_filename = f"{scenario_name}.yaml"
                    saved_path = write_scenario_yaml(new_scenario_data, scenario_filename)
                    
                    st.success(f"✅ New scenario '{scenario_name}' created successfully!")
                    st.info(f"📁 Saved to: {saved_path.name}")
                    
                    # Update the session state to reflect the new scenario
                    st.session_state.loaded_scenario_name = scenario_name
                    
                    # Refresh the page to show the new scenario in the list
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error creating new scenario: {e}")
        
        with col2:
            st.caption("This will create a new YAML file with the current configuration.")
    
    # Load Scenario Functionality
    st.markdown("**Load Existing Scenario**")
    available_scenarios = list_available_scenarios()
    
    if available_scenarios:
        scenario_options = ["Select a scenario..."] + [s.stem for s in available_scenarios]
        selected_scenario = st.selectbox(
            "Choose scenario to load",
            options=scenario_options,
            index=0,
            help="Load an existing scenario configuration",
            key="scenario_selector"
        )
        
        if selected_scenario != "Select a scenario...":
            if st.button(f"Load {selected_scenario}", key=f"load_{selected_scenario}"):
                try:
                    scenario_path = SCENARIOS_DIR / f"{selected_scenario}.yaml"
                    scenario_data = read_scenario_yaml(scenario_path)
                    
                    # Load runspecs from scenario
                    if "runspecs" in scenario_data:
                        rs = scenario_data["runspecs"]
                        editing_state.starttime = float(rs.get("starttime", editing_state.starttime))
                        editing_state.stoptime = float(rs.get("stoptime", editing_state.stoptime))
                        editing_state.dt = float(rs.get("dt", editing_state.dt))
                        mode = str(rs.get("anchor_mode", editing_state.anchor_mode)).strip().lower()
                        if mode in {"sector", "sm"}:
                            editing_state.anchor_mode = mode
                    
                    # Update the session state to reflect what's loaded
                    st.session_state.loaded_scenario_name = selected_scenario
                    
                    st.success(f"✅ Scenario '{selected_scenario}' loaded successfully!")
                    changes_made = True
                    
                except Exception as e:
                    st.error(f"❌ Error loading scenario: {e}")
    else:
        st.info("No existing scenarios found in scenarios/ directory.")
    
    # Reset to Baseline Functionality
    st.markdown("**Reset to Baseline**")
    st.caption("Baseline is a 'special' scenario that represents the default model configuration.")
    
    if st.button("Reset to Baseline", type="secondary", key="reset_baseline"):
        try:
            # Load baseline scenario if it exists
            baseline_path = SCENARIOS_DIR / "baseline.yaml"
            if baseline_path.exists():
                baseline_data = read_scenario_yaml(baseline_path)
                if "runspecs" in baseline_data:
                    rs = baseline_data["runspecs"]
                    editing_state.starttime = float(rs.get("starttime", 2025.0))
                    editing_state.stoptime = float(rs.get("stoptime", 2032.0))
                    editing_state.dt = float(rs.get("dt", 0.25))
                    editing_state.anchor_mode = str(rs.get("anchor_mode", "sector"))
                
                st.success("✅ Reset to baseline configuration!")
                st.session_state.loaded_scenario_name = "baseline"
                changes_made = True
            else:
                # Use default values if no baseline exists
                editing_state.starttime = 2025.0
                editing_state.stoptime = 2032.0
                editing_state.dt = 0.25
                editing_state.anchor_mode = "sector"
                
                # Update session state to reflect default
                st.session_state.loaded_scenario_name = "default"
                
                st.success("✅ Reset to default configuration!")
                changes_made = True
                
        except Exception as e:
            st.error(f"❌ Error resetting to baseline: {e}")
    
    # Validation Section
    st.markdown("**Validation**")
    errors: list[str] = []
    
    if editing_state.dt <= 0:
        errors.append("dt must be positive")
    if editing_state.starttime >= editing_state.stoptime:
        errors.append("starttime must be less than stoptime")
    if editing_state.anchor_mode not in {"sector", "sm"}:
        errors.append("anchor_mode must be 'sector' or 'sm'")
    
    # Display validation errors
    if errors:
        for error in errors:
            st.error(f"❌ {error}")
    else:
        st.success("✅ All runtime parameters are valid")
    
    # Save Button Section
    st.markdown("**Save Configuration**")
    
    # Show unsaved changes indicator
    if changes_made:
        st.warning("⚠️ You have unsaved changes. Click Save to apply them.")
    
    # Save button with change protection
    col1, col2 = st.columns([1, 3])
    with col1:
        save_clicked = st.button(
            "💾 Save Changes", 
            type="primary",
            disabled=not changes_made,
            help="Save the current configuration changes"
        )
    
    with col2:
        if changes_made:
            st.caption("Changes will be saved to the current scenario configuration.")
        else:
            st.caption("No changes to save.")
    
    # Handle save action
    if save_clicked and changes_made:
        try:
            # Update the original state
            state.starttime = editing_state.starttime
            state.stoptime = editing_state.stoptime
            state.dt = editing_state.dt
            state.anchor_mode = editing_state.anchor_mode
            
            # Call save callback if provided
            if on_save_callback:
                on_save_callback(state)
            
            st.success("✅ Configuration saved successfully!")
            changes_made = False
            
        except Exception as e:
            st.error(f"❌ Error saving configuration: {e}")
    
    # Summary Section
    st.markdown("**Current Configuration Summary**")
    
    # Current Scenario Status Display - shows actual loaded scenario
    st.markdown("**📋 Current Scenario Status**")
    if st.session_state.loaded_scenario_name != "working_scenario":
        st.success(f"📁 **Loaded Scenario**: {st.session_state.loaded_scenario_name}")
        st.caption("This scenario is currently loaded and active. Changes will be applied to this scenario.")
    else:
        st.info("📝 **Default Scenario**: working_scenario")
        st.caption("Using the default scenario name. You can change this to create a new scenario.")
    
    summary_data = {
        "Parameter": ["Start Time", "Stop Time", "dt", "Anchor Mode"],
        "Value": [
            f"{editing_state.starttime:.2f} years",
            f"{editing_state.stoptime:.2f} years", 
            f"{editing_state.dt:.2f} years",
            editing_state.anchor_mode.upper()
        ]
    }
    st.dataframe(summary_data, use_container_width=True)
    
    # Return the updated state and any errors
    return editing_state, errors


__all__ = ["render_runspecs_form"]
