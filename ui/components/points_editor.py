from __future__ import annotations

"""
Enhanced Time-series (points) editor component for Streamlit.

Phase 6 Implementation: Tabular format with grouped tables for different point types.
Features:
- Years as columns with proper time handling
- Row-based point entry and editing
- Grouped tables for different point categories
- Bulk point operations
- Auto-completion and validation
- Data import/export capabilities

This component is now framework-agnostic and works with the new state management system.
"""

from typing import List, Tuple, Dict, Optional, Set
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Import from the new framework-agnostic business logic
from ui.state import ScenarioOverridesState


class TabularPointsEditor:
    """Enhanced tabular points editor with grouped tables."""
    
    def __init__(self):
        """Initialize the tabular points editor."""
        self.time_range = (2020.0, 2030.0)  # Default time range
        self.time_step = 0.25  # Quarterly steps
        self.point_categories = {
            "Pricing": ["price_"],
            "Capacity": ["max_capacity_"],
            "Other": []  # For any other point types
        }
    
    def _generate_time_columns(self, start_year: float, end_year: float, step: float) -> List[float]:
        """Generate time column headers.
        
        Args:
            start_year: Start year
            end_year: End year
            step: Time step (e.g., 0.25 for quarterly)
            
        Returns:
            List of time values for columns
        """
        times = []
        current = start_year
        while current <= end_year:
            times.append(round(current, 2))
            current += step
        return times
    
    def _categorize_points(self, points: Set[str]) -> Dict[str, List[str]]:
        """Categorize points by type.
        
        Args:
            points: Set of point names
            
        Returns:
            Dictionary mapping categories to lists of point names
        """
        categorized = {category: [] for category in self.point_categories.keys()}
        
        for point in points:
            categorized_flag = False
            for category, prefixes in self.point_categories.items():
                if any(point.startswith(prefix) for prefix in prefixes):
                    categorized[category].append(point)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                categorized["Other"].append(point)
        
        return categorized
    
    def _create_points_dataframe(self, point_name: str, series: List[Tuple[float, float]], 
                                time_columns: List[float]) -> pd.DataFrame:
        """Create a DataFrame for a single point series.
        
        Args:
            point_name: Name of the point
            series: List of (time, value) tuples
            time_columns: List of time values for columns
            
        Returns:
            DataFrame with time columns and point values
        """
        # Create DataFrame with time columns
        df = pd.DataFrame(index=[point_name], columns=time_columns)
        df = df.fillna(np.nan)
        
        # Fill in existing values
        for time, value in series:
            if time in time_columns:
                df.loc[point_name, time] = value
        
        return df
    
    def _update_series_from_dataframe(self, df: pd.DataFrame, point_name: str) -> List[Tuple[float, float]]:
        """Update series data from DataFrame.
        
        Args:
            df: DataFrame with point values
            time_columns: List of time values
            
        Returns:
            Updated series as list of (time, value) tuples
        """
        series = []
        for col in df.columns:
            value = df.loc[point_name, col]
            if pd.notna(value) and value != 0:  # Only include non-null, non-zero values
                series.append((float(col), float(value)))
        
        # Sort by time
        series.sort(key=lambda x: x[0])
        return series
    
    def _render_point_table(self, point_name: str, series: List[Tuple[float, float]], 
                           time_columns: List[float], on_update: callable) -> pd.DataFrame:
        """Render a table for a single point.
        
        Args:
            point_name: Name of the point
            series: Current series data
            time_columns: Time columns for the table
            on_update: Callback for updates
            
        Returns:
            Updated DataFrame
        """
        st.markdown(f"#### {point_name}")
        
        # Create DataFrame
        df = self._create_points_dataframe(point_name, series, time_columns)
        
        # Display current values summary
        if series:
            times = [t for t, _ in series]
            values = [v for _, v in series]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Points", len(series))
            with col2:
                st.metric("Time Range", f"{min(times):.2f} - {max(times):.2f}")
            with col3:
                st.metric("Min Value", f"{min(values):.4f}")
            with col4:
                st.metric("Max Value", f"{max(values):.4f}")
        
        # Editable table
        edited_df = st.data_editor(
            df,
            key=f"points_table_{point_name}",
            use_container_width=True,
            num_rows="dynamic",
            help=f"Edit values for {point_name}. Use 0 or leave empty to remove points."
        )
        
        # Add new point controls
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            new_time = st.selectbox("Time", time_columns, key=f"new_time_{point_name}")
        with col2:
            new_value = st.number_input("Value", value=0.0, step=0.01, key=f"new_value_{point_name}")
        with col3:
            if st.button("Add Point", key=f"add_point_{point_name}"):
                if new_value != 0:
                    edited_df.loc[point_name, new_time] = new_value
                    # Update series and callback
                    updated_series = self._update_series_from_dataframe(edited_df, point_name)
                    if on_update:
                        on_update(updated_series)
                    st.rerun()
        
        return edited_df
    
    def _render_category_table(self, category: str, points: List[str], 
                              current_points: Dict[str, List[Tuple[float, float]]],
                              time_columns: List[float], on_update: callable) -> None:
        """Render a table for a category of points.
        
        Args:
            category: Category name
            points: List of point names in this category
            current_points: Current points data
            time_columns: Time columns for tables
            on_update: Callback for updates
        """
        if not points:
            return
        
        st.markdown(f"### {category} Points")
        
        # Create tabs for each point in the category
        if len(points) > 1:
            point_tabs = st.tabs(points)
        else:
            point_tabs = [st.container()]
            st.markdown(f"**{points[0]}**")
        
        for i, point_name in enumerate(points):
            series = current_points.get(point_name, [])
            
            # Create callback for this specific point
            def create_update_callback(point):
                def update_callback(new_series):
                    current_points[point] = new_series
                    if on_update:
                        on_update(current_points)
                return update_callback
            
            update_callback = create_update_callback(point_name)
            
            with point_tabs[i]:
                edited_df = self._render_point_table(
                    point_name, series, time_columns, update_callback
                )
                
                # Update series when table changes
                if not edited_df.equals(self._create_points_dataframe(point_name, series, time_columns)):
                    updated_series = self._update_series_from_dataframe(edited_df, point_name)
                    update_callback(updated_series)
    
    def render_tabular_editor(self, state: ScenarioOverridesState, permissible_points: List[str],
                             on_points_update: callable = None) -> Dict[str, List[Tuple[float, float]]]:
        """Render the enhanced tabular points editor.
        
        Args:
            state: Current ScenarioOverridesState containing points overrides
            permissible_points: List of permissible point keys
            on_points_update: Callback function to update state when points change
            
        Returns:
            Updated points dictionary
        """
        st.subheader("Enhanced Tabular Points Editor")
        st.caption("Edit time-series data in table format with years as columns. Use 0 or leave empty to remove points.")
        
        # Get current points from state
        current_points = dict(state.points)
        
        # Time range configuration
        st.markdown("### Time Configuration")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_year = st.number_input("Start Year", value=2020.0, step=0.25, key="start_year")
        with col2:
            end_year = st.number_input("End Year", value=2030.0, step=0.25, key="end_year")
        with col3:
            time_step = st.selectbox("Time Step", [0.25, 0.5, 1.0], index=0, key="time_step")
        
        # Generate time columns
        time_columns = self._generate_time_columns(start_year, end_year, time_step)
        
        # Filter and search
        st.markdown("### Point Selection")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            query = st.text_input("Filter points", value="", key="points_filter").strip().lower()
            filtered = [k for k in permissible_points if query in k.lower()]
        
        with col2:
            show_empty = st.checkbox("Show empty points", value=False)
        
        # Apply filters
        if not show_empty:
            filtered = [k for k in filtered if k in current_points and current_points[k]]
        
        # Guard against empty option set
        if not filtered:
            st.info("No points match the current filter.")
            return current_points
        
        # Categorize points
        categorized_points = self._categorize_points(set(filtered))
        
        # Render category tables
        for category, points in categorized_points.items():
            if points:
                self._render_category_table(
                    category, points, current_points, time_columns, on_points_update
                )
        
        # Global operations
        st.markdown("---")
        st.markdown("### Global Operations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Clear All Points", type="secondary"):
                current_points.clear()
                if on_points_update:
                    on_points_update(current_points)
                st.rerun()
        
        with col2:
            if st.button("Export Points", type="primary"):
                st.session_state.export_points = True
        
        with col3:
            if st.button("Import Points", type="primary"):
                st.session_state.import_points = True
        
        # Export functionality
        if st.session_state.get("export_points", False):
            st.session_state.export_points = False
            
            # Create export data
            export_data = []
            for point_name, series in current_points.items():
                if series:
                    for time, value in series:
                        export_data.append({
                            "Point": point_name,
                            "Time": time,
                            "Value": value
                        })
            
            if export_data:
                export_df = pd.DataFrame(export_data)
                csv_data = export_df.to_csv(index=False)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                st.download_button(
                    label="Download Points CSV",
                    data=csv_data,
                    file_name=f"points_export_{timestamp}.csv",
                    mime="text/csv"
                )
        
        # Import functionality
        if st.session_state.get("import_points", False):
            st.session_state.import_points = False
            
            uploaded_file = st.file_uploader(
                "Upload Points CSV",
                type=['csv'],
                help="CSV should have columns: Point, Time, Value"
            )
            
            if uploaded_file is not None:
                try:
                    import_df = pd.read_csv(uploaded_file)
                    
                    if set(import_df.columns) >= {"Point", "Time", "Value"}:
                        # Process imported data
                        imported_points = {}
                        for _, row in import_df.iterrows():
                            point = row["Point"]
                            time_val = float(row["Time"])
                            value = float(row["Value"])
                            
                            if point not in imported_points:
                                imported_points[point] = []
                            
                            imported_points[point].append((time_val, value))
                        
                        # Update current points
                        current_points.update(imported_points)
                        
                        if on_points_update:
                            on_points_update(current_points)
                        
                        st.success(f"Successfully imported {len(imported_points)} points!")
                        st.rerun()
                    else:
                        st.error("CSV must have columns: Point, Time, Value")
                except Exception as e:
                    st.error(f"Error importing points: {e}")
        
        return current_points


def render_points_editor(
    state: ScenarioOverridesState, 
    permissible_points: List[str],
    on_points_update: callable = None
) -> ScenarioOverridesState:
    """Render the enhanced points editor and return updated points overrides.

    Args:
        state: Current ScenarioOverridesState containing points overrides
        permissible_points: List of permissible point keys
        on_points_update: Callback function to update state when points change

    Returns:
        Updated ScenarioOverridesState with modified points
    """
    # Create tabular editor instance
    editor = TabularPointsEditor()
    
    # Render the enhanced editor and update the state
    updated_points = editor.render_tabular_editor(state, permissible_points, on_points_update)
    state.points = updated_points
    return state


def render_points_summary(points: Dict[str, List[Tuple[float, float]]]) -> None:
    """Render a comprehensive summary view of points overrides.
    
    Args:
        points: Dictionary of points overrides to display
    """
    if not points:
        st.info("No points overridden")
        return
    
    st.markdown("### Enhanced Points Summary")
    
    # Create summary dataframe
    summary_data = []
    total_points = 0
    time_ranges = []
    value_ranges = []
    
    for key, series in points.items():
        if series:
            times = [t for t, _ in series]
            values = [v for _, v in series]
            
            summary_data.append({
                "Point": key,
                "Points": len(series),
                "Time Range": f"{min(times):.1f} - {max(times):.1f}",
                "Value Range": f"{min(values):.4f} - {max(values):.4f}",
                "Avg Value": f"{np.mean(values):.4f}",
                "Std Dev": f"{np.std(values):.4f}"
            })
            
            total_points += len(series)
            time_ranges.extend(times)
            value_ranges.extend(values)
    
    if summary_data:
        # Display summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Points", total_points)
        with col2:
            st.metric("Unique Series", len(summary_data))
        with col3:
            if time_ranges:
                st.metric("Global Time Range", f"{min(time_ranges):.1f} - {max(time_ranges):.1f}")
        with col4:
            if value_ranges:
                st.metric("Global Value Range", f"{min(value_ranges):.4f} - {max(value_ranges):.4f}")
        
        # Display detailed summary table
        df = pd.DataFrame(summary_data)
        st.dataframe(df, use_container_width=True)
        
        # Visualizations
        if len(summary_data) > 1:
            st.markdown("### Summary Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Points per series chart
                points_counts = [row["Points"] for row in summary_data]
                series_names = [row["Point"] for row in summary_data]
                
                chart_data = pd.DataFrame({
                    "Series": series_names,
                    "Points": points_counts
                })
                
                st.bar_chart(chart_data.set_index("Series"))
                st.caption("Points per series")
            
            with col2:
                # Value distribution
                if value_ranges:
                    st.histogram(value_ranges, bins=20)
                    st.caption("Value distribution across all points")


__all__ = ["render_points_editor", "render_points_summary"]
