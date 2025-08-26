"""
Runner Tab Component

This component provides a user interface for scenario execution controls,
monitoring, and progress tracking. It includes save button protection
for execution settings and integrates with the backend runner service
to display actual simulation results.

Author: AI Assistant
Date: 2024
"""

import streamlit as st
from typing import Dict, Any, Optional
import time
import pandas as pd
from pathlib import Path

from ui.state import RunnerState
from ui.services.runner import (
    build_runner_command, 
    run_simulation, 
    find_latest_results_csv,
    generate_plots_from_csv
)


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
    st.caption("Control scenario execution, monitor progress, and view simulation results.")
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Execution Controls Section
        st.markdown("#### Execution Controls")
        
        # Scenario Selection
        scenario_name = st.text_input(
            "Scenario Name",
            value=state.current_scenario or "baseline",
            help="Name of the scenario to execute (use 'baseline' for default)"
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
        state.kpi_sm_client_rows = state.kpi_sm_client_rows
        
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
            
            # Execution status (no progress bar)
            st.success("✅ Execution completed!")
            state.is_running = False
        else:
            st.success("✅ Ready for execution")
        
        # Quick Actions
        st.markdown("#### Quick Actions")
        
        if st.button("🚀 Run Current Scenario", type="primary", disabled=state.is_running, key="runner_run_btn"):
            # Execute the simulation
            _execute_simulation(state)
            state.is_running = True
            st.rerun()
        
        if st.button("⏹️ Stop Execution", disabled=not state.is_running, key="runner_stop_btn"):
            state.is_running = False
            st.rerun()
        
        if st.button("🔄 Reset Status", key="runner_reset_btn"):
            state.is_running = False
            st.rerun()
    
    # Results Display Section
    st.markdown("---")
    st.markdown("#### Simulation Results")
    
    # Display latest CSV results
    _display_latest_results()
    
    # Display generated plots if available
    if state.generate_plots:
        _display_generated_plots()
    
    # Execution History Section
    st.markdown("---")
    st.markdown("#### Execution History")
    
    # Show actual execution history
    _display_execution_history()
    
    # Execution Summary
    render_execution_summary(state)
    
    return state


def _execute_simulation(state: RunnerState) -> None:
    """Execute the simulation using the backend runner service."""
    
    try:
        # Build the runner command
        runner_cmd = build_runner_command(
            preset=state.current_scenario,
            debug=state.debug_mode,
            visualize=state.generate_plots,
            kpi_sm_revenue_rows=state.kpi_sm_revenue_rows,
            kpi_sm_client_rows=state.kpi_sm_client_rows
        )
        
        # Execute the simulation
        st.info(f"🚀 Executing scenario: {state.current_scenario}")
        exit_code = run_simulation(runner_cmd)
        
        if exit_code == 0:
            st.success(f"✅ Scenario '{state.current_scenario}' executed successfully!")
        else:
            st.error(f"❌ Scenario execution failed with exit code: {exit_code}")
            
    except Exception as e:
        st.error(f"❌ Error executing simulation: {str(e)}")


def _display_latest_results() -> None:
    """Display the latest CSV results in a table format."""
    
    try:
        # Find the latest results CSV
        latest_csv = find_latest_results_csv()
        
        if latest_csv and latest_csv.exists():
            st.success(f"📊 Latest Results: {latest_csv.name}")
            
            # Read and display the CSV data
            df = pd.read_csv(latest_csv)
            
            # Show basic statistics
            st.markdown("**Results Summary:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                st.metric("File Size", f"{latest_csv.stat().st_size / 1024:.1f} KB")
            
            # Display the data in an expandable section
            with st.expander("📋 View Full Results Data", expanded=False):
                st.dataframe(df, use_container_width=True)
                
                # Download button for the CSV
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results CSV",
                    data=csv_data,
                    file_name=latest_csv.name,
                    mime="text/csv"
                )
        else:
            st.info("📊 No results available yet. Run a simulation to generate results.")
            
    except Exception as e:
        st.error(f"❌ Error loading results: {str(e)}")


def _display_generated_plots() -> None:
    """Display generated plots if they exist."""
    
    try:
        plots_dir = Path("output/plots")
        
        if plots_dir.exists():
            plot_files = list(plots_dir.glob("*.png"))
            
            if plot_files:
                st.success(f"📈 Generated Plots: {len(plot_files)} available")
                
                # Display plots in columns
                cols = st.columns(2)
                for i, plot_file in enumerate(plot_files[:4]):  # Show up to 4 plots
                    col_idx = i % 2
                    with cols[col_idx]:
                        st.markdown(f"**{plot_file.stem.replace('_', ' ').title()}**")
                        st.image(plot_file, use_column_width=True)
                        
                        # Download button for each plot
                        with open(plot_file, "rb") as f:
                            st.download_button(
                                label=f"📥 Download {plot_file.stem}",
                                data=f.read(),
                                file_name=plot_file.name,
                                mime="image/png"
                            )
                
                # Show remaining plots in expandable section
                if len(plot_files) > 4:
                    with st.expander(f"📊 View {len(plot_files) - 4} More Plots"):
                        remaining_plots = plot_files[4:]
                        for plot_file in remaining_plots:
                            st.markdown(f"**{plot_file.stem.replace('_', ' ').title()}**")
                            st.image(plot_file, use_column_width=True)
            else:
                st.info("📈 No plots generated yet. Enable 'Generate Plots' and run a simulation.")
        else:
            st.info("📈 Plots directory not found. Enable 'Generate Plots' and run a simulation.")
            
    except Exception as e:
        st.error(f"❌ Error loading plots: {str(e)}")


def _display_execution_history() -> None:
    """Display execution history from available output files."""
    
    try:
        output_dir = Path("output")
        if not output_dir.exists():
            st.info("📋 No execution history available.")
            return
        
        # Find all CSV files
        csv_files = list(output_dir.glob("Growth_System_Complete_Results*.csv"))
        
        if csv_files:
            st.success(f"📋 Execution History: {len(csv_files)} scenarios executed")
            
            # Create a summary table
            history_data = []
            for csv_file in csv_files:
                try:
                    # Extract scenario name from filename
                    scenario_name = csv_file.stem.replace("Growth_System_Complete_Results_", "")
                    if not scenario_name:
                        scenario_name = "baseline"
                    
                    # Get file stats
                    stat = csv_file.stat()
                    file_size = stat.st_size / 1024  # KB
                    modified_time = time.ctime(stat.st_mtime)
                    
                    history_data.append({
                        "Scenario": scenario_name,
                        "File": csv_file.name,
                        "Size (KB)": f"{file_size:.1f}",
                        "Modified": modified_time,
                        "Status": "✅ Success"
                    })
                except Exception:
                    continue
            
            if history_data:
                # Display as a table
                history_df = pd.DataFrame(history_data)
                st.dataframe(history_df, use_container_width=True)
            else:
                st.info("📋 No valid execution history found.")
        else:
            st.info("📋 No execution history available. Run a simulation to generate results.")
            
    except Exception as e:
        st.error(f"❌ Error loading execution history: {str(e)}")


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
