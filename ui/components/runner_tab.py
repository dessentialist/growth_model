"""
Runner Tab Component

This component provides a user interface for scenario execution controls,
monitoring, and progress tracking. It includes save button protection
for execution settings.

Author: AI Assistant
Date: 2024
"""

import streamlit as st
from typing import Dict, Any
import time

from ui.state import RunnerState


def render_runner_tab(
    state: RunnerState,
    on_save: callable = None
) -> RunnerState:
    """
    Render the runner tab for scenario execution and monitoring.
    
    Args:
        state: Current runner state
        on_save: Optional callback function when changes are saved
        
    Returns:
        Updated runner state
    """
    
    st.markdown("### Scenario Execution & Monitoring")
    st.caption("Control scenario execution, monitor progress, and manage execution settings.")
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Execution Controls Section
        st.markdown("#### Execution Controls")
        
        # Scenario Selection
        scenario_name = st.text_input(
            "Scenario Name",
            value=state.current_scenario or "working_scenario",
            help="Name of the scenario to execute"
        )
        state.current_scenario = scenario_name
        
        # Execution Settings
        st.markdown("#### Execution Settings")
        
        debug_mode = st.checkbox(
            "Debug Mode",
            value=state.debug_mode,
            help="Enable debug output during execution"
        )
        state.debug_mode = debug_mode
        
        generate_plots = st.checkbox(
            "Generate Plots",
            value=state.generate_plots,
            help="Generate visualization plots after execution"
        )
        state.generate_plots = generate_plots
        
        kpi_sm_revenue_rows = st.checkbox(
            "KPI SM Revenue Rows",
            value=state.kpi_sm_revenue_rows,
            help="Include sector-material revenue rows in KPI output"
        )
        state.kpi_sm_revenue_rows = kpi_sm_revenue_rows
        
        kpi_sm_client_rows = st.checkbox(
            "KPI SM Client Rows",
            value=state.kpi_sm_client_rows,
            help="Include sector-material client rows in KPI output"
        )
        state.kpi_sm_client_rows = kpi_sm_client_rows
        
        # Save button for execution settings
        st.markdown("---")
        st.markdown("#### Save Execution Settings")
        
        # Check for unsaved changes
        has_changes = _check_for_unsaved_changes(state)
        state.has_unsaved_changes = has_changes
        
        if has_changes:
            st.warning("⚠️ You have unsaved execution settings. Click Save to persist your changes.")
        
        if st.button("💾 Save Execution Settings", type="primary", disabled=not has_changes, key="runner_save_btn"):
            if on_save:
                on_save(state)
            st.success("✅ Execution settings saved successfully!")
            state.has_unsaved_changes = False
            st.rerun()
    
    with col2:
        # Execution Status Section
        st.markdown("#### Execution Status")
        
        # Current Status
        if state.is_running:
            st.info("🔄 Scenario is currently running...")
            
            # Progress bar (simulated for now)
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            # Simulate progress updates
            for i in range(101):
                time.sleep(0.01)  # Small delay for demo
                progress_bar.progress(i)
                progress_text.text(f"Progress: {i}%")
                if i == 100:
                    break
            
            st.success("✅ Execution completed!")
            state.is_running = False
        else:
            st.success("✅ Ready for execution")
        
        # Quick Actions
        st.markdown("#### Quick Actions")
        
        if st.button("🚀 Run Current Scenario", type="primary", disabled=state.is_running, key="runner_run_btn"):
            state.is_running = True
            st.rerun()
        
        if st.button("⏹️ Stop Execution", disabled=not state.is_running, key="runner_stop_btn"):
            state.is_running = False
            st.rerun()
        
        if st.button("🔄 Reset Status", key="runner_reset_btn"):
            state.is_running = False
            st.rerun()
    
    # Execution History Section
    st.markdown("---")
    st.markdown("#### Execution History")
    
    # Placeholder for execution history
    if not state.is_running:
        st.info("📊 Execution history will appear here after running scenarios.")
        
        # Sample execution history (for demonstration)
        with st.expander("📋 Sample Execution History"):
            st.markdown("""
            | Scenario | Status | Start Time | Duration | Results |
            |----------|--------|------------|----------|---------|
            | baseline | ✅ Success | 2024-01-15 10:30 | 2m 15s | [View Results] |
            | high_capacity | ✅ Success | 2024-01-15 09:15 | 1m 45s | [View Results] |
            | price_shock | ⚠️ Warnings | 2024-01-14 16:20 | 3m 10s | [View Results] |
            """)
    
    # Execution Summary
    render_execution_summary(state)
    
    return state


def _check_for_unsaved_changes(state: RunnerState) -> bool:
    """Check if there are any unsaved changes in the execution settings."""
    
    # For now, we'll use the has_unsaved_changes flag
    # In a more sophisticated implementation, we could compare against original values
    return state.has_unsaved_changes


def render_execution_summary(state: RunnerState):
    """Render a summary of the current execution configuration."""
    
    st.markdown("### Execution Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Scenario", state.current_scenario or "None")
        st.caption("Scenario to be executed")
    
    with col2:
        status = "🔄 Running" if state.is_running else "✅ Ready"
        st.metric("Status", status)
        st.caption("Current execution state")
    
    with col3:
        settings_count = sum([
            state.debug_mode,
            state.generate_plots,
            state.kpi_sm_revenue_rows,
            state.kpi_sm_client_rows
        ])
        st.metric("Active Settings", settings_count)
        st.caption("Number of enabled options")
    
    # Show execution configuration
    st.markdown("**Execution Configuration:**")
    
    config_cols = st.columns(4)
    with config_cols[0]:
        st.caption(f"Debug Mode: {'✅' if state.debug_mode else '❌'}")
    with config_cols[1]:
        st.caption(f"Generate Plots: {'✅' if state.generate_plots else '❌'}")
    with config_cols[2]:
        st.caption(f"SM Revenue Rows: {'✅' if state.kpi_sm_revenue_rows else '❌'}")
    with config_cols[3]:
        st.caption(f"SM Client Rows: {'✅' if state.kpi_sm_client_rows else '❌'}")


def get_execution_config_for_backend(state: RunnerState) -> Dict[str, Any]:
    """Convert runner state to backend-compatible execution configuration."""
    
    config = {
        "scenario_name": state.current_scenario,
        "debug_mode": state.debug_mode,
        "generate_plots": state.generate_plots,
        "kpi_sm_revenue_rows": state.kpi_sm_revenue_rows,
        "kpi_sm_client_rows": state.kpi_sm_client_rows
    }
    
    return config
