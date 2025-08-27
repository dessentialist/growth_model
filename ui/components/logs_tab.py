"""
Logs Tab Component

This component provides a user interface for simulation logs display,
filtering, and export functionality. It reads real logs from the
simulation engine and provides comprehensive log management.

Author: Darpan Shah
Date: 2024
"""

import streamlit as st
from typing import Dict, Any, List
import datetime
from pathlib import Path

from ui.state import LogsState
from ui.services.runner import read_log_tail


def render_logs_tab(
    state: LogsState,
    on_save: callable = None
) -> LogsState:
    """
    Render the logs tab for simulation logs display and management.
    
    Args:
        state: Current logs state
        on_save: Optional callback function when changes are saved
        
    Returns:
        Updated logs state
    """
    
    st.markdown("### Simulation Logs & Monitoring")
    st.caption("View real simulation logs, configure log display, and export log data.")
    
    # Create two columns for layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Log Configuration Section
        st.markdown("#### Log Configuration")
        
        # Log level selection
        log_level = st.selectbox(
            "Log Level",
            options=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
            index=1,  # Default to INFO
            help="Minimum log level to display"
        )
        state.log_level = log_level
        
        # Max lines selection
        max_log_lines = st.slider(
            "Maximum Log Lines",
            min_value=100,
            max_value=2000,
            value=state.max_log_lines,
            step=100,
            help="Maximum number of log lines to display"
        )
        state.max_log_lines = max_log_lines
        
        # Auto refresh toggle
        auto_refresh = st.checkbox(
            "Auto Refresh",
            value=state.auto_refresh,
            help="Automatically refresh logs during execution"
        )
        state.auto_refresh = auto_refresh
        
        # Log content display
        st.markdown("#### Log Content")
        
        # Read real logs from the simulation engine
        real_logs = _read_and_parse_real_logs(state.log_level, state.max_log_lines)
        
        if real_logs:
            st.success(f"📋 Loaded {len(real_logs)} log entries from simulation engine")
            
            # Display logs in a scrollable container
            log_container = st.container()
            with log_container:
                for log_entry in real_logs:
                    _render_log_entry(log_entry)
        else:
            st.info("📋 No logs available yet. Run a simulation to generate logs.")
            st.caption("Logs will appear here after executing scenarios.")
        
        # Log export functionality
        if real_logs:
            st.markdown("---")
            st.markdown("#### Export Logs")
            
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                if st.button("📥 Download Logs (TXT)", key="logs_download_txt_btn"):
                    _download_logs_as_txt(real_logs)
            
            with col_export2:
                if st.button("📊 Download Logs (CSV)", key="logs_download_csv_btn"):
                    _download_logs_as_csv(real_logs)
    
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
        
        if real_logs:
            total_logs = len(real_logs)
            error_count = len([log for log in real_logs if log["level"] == "ERROR"])
            warning_count = len([log for log in real_logs if log["level"] == "WARNING"])
            info_count = len([log for log in real_logs if log["level"] == "INFO"])
            debug_count = len([log for log in real_logs if log["level"] == "DEBUG"])
            
            st.metric("Total Logs", total_logs)
            st.metric("Errors", error_count)
            st.metric("Warnings", warning_count)
            st.metric("Info", info_count)
            if debug_count > 0:
                st.metric("Debug", debug_count)
        else:
            st.metric("Total Logs", 0)
            st.metric("Errors", 0)
            st.metric("Warnings", 0)
            st.metric("Info", 0)
    
    # Log Summary
    if real_logs:
        render_logs_summary(state, real_logs)
    
    return state


def _read_and_parse_real_logs(log_level: str, max_lines: int) -> List[Dict]:
    """Read and parse real logs from the simulation engine."""
    
    try:
        # Read real logs using the existing service
        raw_log_lines = read_log_tail(max_lines)
        
        if not raw_log_lines:
            return []
        
        # Parse log lines into structured format
        parsed_logs = []
        for line in raw_log_lines:
            log_entry = _parse_log_line(line)
            if log_entry and _should_include_log(log_entry, log_level):
                parsed_logs.append(log_entry)
        
        # Sort by timestamp (newest first)
        parsed_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return parsed_logs
        
    except Exception as e:
        st.error(f"❌ Error reading logs: {str(e)}")
        return []


def _parse_log_line(log_line: str) -> Dict:
    """Parse a single log line into structured format."""
    
    try:
        # Expected format: "2025-08-27 01:51:17,158 | INFO | src.phase1_data | Loading Phase 1 inputs from JSON: inputs.json"
        parts = log_line.split(" | ")
        
        if len(parts) >= 4:
            timestamp_str = parts[0]
            level = parts[1]
            source = parts[2]
            message = " | ".join(parts[3:])
            
            # Parse timestamp
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            
            return {
                "timestamp": timestamp,
                "level": level,
                "source": source,
                "message": message
            }
        else:
            # Fallback for non-standard log lines
            return {
                "timestamp": datetime.datetime.now(),
                "level": "INFO",
                "source": "unknown",
                "message": log_line
            }
            
    except Exception:
        # Return None for unparseable lines
        return None


def _should_include_log(log_entry: Dict, log_level: str) -> bool:
    """Check if log entry should be included based on log level filter."""
    
    if log_level == "ALL":
        return True
    
    level_priority = {
        "ERROR": 4,
        "WARNING": 3,
        "INFO": 2,
        "DEBUG": 1
    }
    
    entry_priority = level_priority.get(log_entry["level"], 0)
    filter_priority = level_priority.get(log_level, 0)
    
    return entry_priority >= filter_priority


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
    
    # Create DataFrame
    data = []
    for log in logs:
        data.append({
            "Timestamp": log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "Level": log["level"],
            "Source": log["source"],
            "Message": log["message"]
        })
    
    df = pd.DataFrame(data)
    csv_data = df.to_csv(index=False)
    
    # Create download button
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name=f"simulation_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def _check_for_unsaved_changes(state: LogsState) -> bool:
    """Check if there are any unsaved changes in the log configuration."""
    
    # For now, we'll use the has_unsaved_changes flag
    # In a more sophisticated implementation, we could compare against original values
    return state.has_unsaved_changes


def render_logs_summary(state: LogsState, logs: List[Dict]):
    """Render a summary of the current logs configuration."""
    
    st.markdown("### Log Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Log Level", state.log_level)
        st.caption("Minimum level displayed")
    
    with col2:
        st.metric("Max Lines", state.max_log_lines)
        st.caption("Maximum lines to show")
    
    with col3:
        auto_refresh_status = "✅ Enabled" if state.auto_refresh else "❌ Disabled"
        st.metric("Auto Refresh", auto_refresh_status)
        st.caption("Automatic log updates")
    
    # Show log file information
    st.markdown("**Log File Information:**")
    
    log_file_path = Path("logs/run.log")
    if log_file_path.exists():
        file_size = log_file_path.stat().st_size / 1024  # KB
        modified_time = datetime.datetime.fromtimestamp(log_file_path.stat().st_mtime)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"File: {log_file_path.name}")
        with col2:
            st.caption(f"Size: {file_size:.1f} KB")
        with col3:
            st.caption(f"Modified: {modified_time.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.warning("⚠️ Log file not found. Run a simulation to generate logs.")


def get_logs_config_for_backend(state: LogsState) -> Dict[str, Any]:
    """Convert logs state to backend-compatible configuration."""
    
    config = {
        "log_level": state.log_level,
        "max_log_lines": state.max_log_lines,
        "auto_refresh": state.auto_refresh
    }
    
    return config
