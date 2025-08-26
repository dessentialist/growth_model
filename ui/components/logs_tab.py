"""
Logs Tab Component

This component provides a user interface for displaying simulation logs,
filtering, and export functionality. It includes save button protection
for log configuration settings.

Author: AI Assistant
Date: 2024
"""

import streamlit as st
from typing import List, Dict
import datetime
import random

from ui.state import LogsState


def render_logs_tab(
    state: LogsState,
    on_save: callable = None
) -> LogsState:
    """
    Render the logs tab for simulation logs display and monitoring.
    
    Args:
        state: Current logs state
        on_save: Optional callback function when changes are saved
        
    Returns:
        Updated logs state
    """
    
    st.markdown("### Simulation Logs & Monitoring")
    st.caption("Monitor simulation execution logs, filter results, and manage log display settings.")
    
    # Create two columns for layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Log Display Section
        st.markdown("#### Simulation Logs")
        
        # Log filtering controls
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            log_level = st.selectbox(
                "Log Level",
                ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
                index=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"].index(state.log_level),
                help="Filter logs by minimum level"
            )
            state.log_level = log_level
        
        with col_filter2:
            max_lines = st.number_input(
                "Max Lines",
                min_value=100,
                max_value=10000,
                value=state.max_log_lines,
                step=100,
                help="Maximum number of log lines to display"
            )
            state.max_log_lines = max_lines
        
        with col_filter3:
            auto_refresh = st.checkbox(
                "Auto Refresh",
                value=state.auto_refresh,
                help="Automatically refresh logs during execution"
            )
            state.auto_refresh = auto_refresh
        
        # Log content display
        st.markdown("#### Log Content")
        
        # Generate sample logs (in real implementation, this would come from the simulation)
        sample_logs = _generate_sample_logs(state.log_level, state.max_log_lines)
        
        # Display logs in a scrollable container
        log_container = st.container()
        with log_container:
            for log_entry in sample_logs:
                _render_log_entry(log_entry)
        
        # Log export functionality
        st.markdown("---")
        st.markdown("#### Export Logs")
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            if st.button("�� Download Logs (TXT)", key="logs_download_txt_btn"):
                _download_logs_as_txt(sample_logs)
        
        with col_export2:
            if st.button("📊 Download Logs (CSV)", key="logs_download_csv_btn"):
                _download_logs_as_csv(sample_logs)
    
    with col2:
        # Log Configuration Section
        st.markdown("#### Log Configuration")
        
        # Additional log settings
        st.markdown("**Display Options:**")
        
        # Note: These settings are prepared for future implementation
        # Currently they are placeholders for enhanced log display features
        st.checkbox(
            "Show Timestamps",
            value=True,
            help="Display timestamps in log entries"
        )
        
        st.checkbox(
            "Show Log Levels",
            value=True,
            help="Display log level indicators"
        )
        
        st.checkbox(
            "Show Source",
            value=False,
            help="Display log source information"
        )
        
        # Save button for log configuration
        st.markdown("---")
        st.markdown("#### Save Log Settings")
        
        # Check for unsaved changes
        has_changes = _check_for_unsaved_changes(state)
        state.has_unsaved_changes = has_changes
        
        if has_changes:
            st.warning("⚠️ You have unsaved log settings. Click Save to persist your changes.")
        
        if st.button("💾 Save Log Settings", type="primary", disabled=not has_changes, key="logs_save_btn"):
            if on_save:
                on_save(state)
            st.success("✅ Log settings saved successfully!")
            state.has_unsaved_changes = False
            st.rerun()
        
        # Log Statistics
        st.markdown("---")
        st.markdown("#### Log Statistics")
        
        total_logs = len(sample_logs)
        error_count = len([log for log in sample_logs if log["level"] == "ERROR"])
        warning_count = len([log for log in sample_logs if log["level"] == "WARNING"])
        info_count = len([log for log in sample_logs if log["level"] == "INFO"])
        
        st.metric("Total Logs", total_logs)
        st.metric("Errors", error_count)
        st.metric("Warnings", warning_count)
        st.metric("Info", info_count)
    
    # Log Summary
    render_logs_summary(state, sample_logs)
    
    return state


def _generate_sample_logs(log_level: str, max_lines: int) -> List[Dict]:
    """Generate sample log entries for demonstration purposes."""
    
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    if log_level != "ALL":
        start_index = log_levels.index(log_level)
        log_levels = log_levels[start_index:]
    
    sample_messages = [
        "Simulation started successfully",
        "Loading scenario configuration",
        "Validating input parameters",
        "Initializing agent populations",
        "Setting up market dynamics",
        "Running time step calculations",
        "Processing agent interactions",
        "Updating market prices",
        "Calculating KPIs",
        "Generating output plots",
        "Simulation completed successfully",
        "Error in parameter validation",
        "Warning: Low capacity utilization",
        "Info: Market equilibrium reached",
        "Debug: Agent decision process"
    ]
    
    logs = []
    current_time = datetime.datetime.now()
    
    for i in range(min(max_lines, 50)):  # Limit to 50 for demo
        # Generate random log entry
        level = random.choice(log_levels)
        message = random.choice(sample_messages)
        timestamp = current_time - datetime.timedelta(seconds=i*2)
        
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "source": f"simulation_engine_{random.randint(1, 5)}"
        }
        
        logs.append(log_entry)
    
    # Sort by timestamp (newest first)
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return logs


def _render_log_entry(log_entry: Dict):
    """Render a single log entry with appropriate styling."""
    
    # Determine icon based on log level
    level_icons = {
        "ERROR": "❌",
        "WARNING": "⚠️",
        "INFO": "ℹ️",
        "DEBUG": "🔍"
    }
    
    icon = level_icons.get(log_entry["level"], "📝")
    
    # Create columns for layout
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        st.markdown(f"{icon}")
    
    with col2:
        st.markdown(f"**{log_entry['level']}**")
    
    with col3:
        timestamp_str = log_entry["timestamp"].strftime("%H:%M:%S")
        st.markdown(f"`{timestamp_str}` {log_entry['message']}")
    
    # Add separator between log entries
    st.markdown("---")


def _download_logs_as_txt(logs: List[Dict]):
    """Download logs as a text file."""
    
    # Create log content
    log_content = ""
    for log in logs:
        timestamp_str = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        log_content += f"[{timestamp_str}] {log['level']}: {log['message']}\n"
    
    # Create download button
    st.download_button(
        label="📥 Download TXT",
        data=log_content,
        file_name=f"simulation_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )


def _download_logs_as_csv(logs: List[Dict]):
    """Download logs as a CSV file."""
    
    import pandas as pd
    
    # Convert logs to DataFrame
    log_data = []
    for log in logs:
        log_data.append({
            "timestamp": log["timestamp"],
            "level": log["level"],
            "message": log["message"],
            "source": log["source"]
        })
    
    df = pd.DataFrame(log_data)
    
    # Convert to CSV
    csv_data = df.to_csv(index=False)
    
    # Create download button
    st.download_button(
        label="📊 Download CSV",
        data=csv_data,
        file_name=f"simulation_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def _check_for_unsaved_changes(state: LogsState) -> bool:
    """Check if there are any unsaved changes in the log settings."""
    
    # For now, we'll use the has_unsaved_changes flag
    # In a more sophisticated implementation, we could compare against original values
    return state.has_unsaved_changes


def render_logs_summary(state: LogsState, logs: List[Dict]):
    """Render a summary of the current logs configuration."""
    
    st.markdown("### Logs Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Log Level", state.log_level)
        st.caption("Minimum log level displayed")
    
    with col2:
        st.metric("Max Lines", state.max_log_lines)
        st.caption("Maximum log lines shown")
    
    with col3:
        auto_refresh_status = "✅ Enabled" if state.auto_refresh else "❌ Disabled"
        st.metric("Auto Refresh", auto_refresh_status)
        st.caption("Automatic log updates")
    
    # Show log configuration
    st.markdown("**Log Configuration:**")
    
    config_cols = st.columns(2)
    with config_cols[0]:
        st.caption(f"Log Level: {state.log_level}")
        st.caption(f"Max Lines: {state.max_log_lines}")
    with config_cols[1]:
        st.caption(f"Auto Refresh: {'✅' if state.auto_refresh else '❌'}")
        st.caption(f"Total Logs: {len(logs)}")


def get_logs_config_for_backend(state: LogsState) -> Dict:
    """Convert logs state to backend-compatible configuration."""
    
    config = {
        "log_level": state.log_level,
        "max_log_lines": state.max_log_lines,
        "auto_refresh": state.auto_refresh
    }
    
    return config
