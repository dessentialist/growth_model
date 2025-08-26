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
    
    # Scenario Name Input
    scenario_name = st.text_input(
        "Scenario Name",
        value="working_scenario",
        placeholder="Enter scenario name",
        help="Name for the current scenario configuration"
    )
    
    # Load Scenario Functionality
    st.markdown("**Load Existing Scenario**")
    available_scenarios = list_available_scenarios()
    
    if available_scenarios:
        scenario_options = ["Select a scenario..."] + [s.stem for s in available_scenarios]
        selected_scenario = st.selectbox(
            "Choose scenario to load",
            options=scenario_options,
            index=0,
            help="Load an existing scenario configuration"
        )
        
        if selected_scenario != "Select a scenario...":
            if st.button(f"Load {selected_scenario}"):
                try:
                    scenario_path = Path("scenarios") / f"{selected_scenario}.yaml"
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
                    
                    st.success(f"✅ Scenario '{selected_scenario}' loaded successfully!")
                    changes_made = True
                    
                except Exception as e:
                    st.error(f"❌ Error loading scenario: {e}")
    else:
        st.info("No existing scenarios found in scenarios/ directory.")
    
    # Reset to Baseline Functionality
    st.markdown("**Reset to Baseline**")
    st.caption("Baseline is a 'special' scenario that represents the default model configuration.")
    
    if st.button("Reset to Baseline", type="secondary"):
        try:
            # Load baseline scenario if it exists
            baseline_path = Path("scenarios") / "baseline.yaml"
            if baseline_path.exists():
                baseline_data = read_scenario_yaml(baseline_path)
                if "runspecs" in baseline_data:
                    rs = baseline_data["runspecs"]
                    editing_state.starttime = float(rs.get("starttime", 2025.0))
                    editing_state.stoptime = float(rs.get("stoptime", 2032.0))
                    editing_state.dt = float(rs.get("dt", 0.25))
                    editing_state.anchor_mode = str(rs.get("anchor_mode", "sector"))
                
                st.success("✅ Reset to baseline configuration!")
                changes_made = True
            else:
                # Use default values if no baseline exists
                editing_state.starttime = 2025.0
                editing_state.stoptime = 2032.0
                editing_state.dt = 0.25
                editing_state.anchor_mode = "sector"
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
