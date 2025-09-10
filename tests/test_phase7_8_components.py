"""
Tests for Phase 7-8 Components: Lookup Points, Runner, and Logs Tabs

This test file validates the functionality of the newly implemented components
for Phases 7-8 of the Growth Model UI restructuring.

Author: Darpan Shah
Date: 2024
"""

import pytest
import pandas as pd

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from ui.state import (
    LookupPointsState, 
    RunnerState, 
    LogsState,
    SimulationDefinitionsState,
    RunspecsState
)
from ui.components.lookup_points_editor import (
    _generate_year_range,
    _initialize_lookup_points_state,
    _create_production_capacity_dataframe,
    _create_pricing_dataframe,
    get_lookup_points_for_yaml
)
from ui.components.runner_tab import (
    _check_for_unsaved_changes,
    get_execution_config_for_backend
)
from ui.components.logs_tab import (
    get_logs_config_for_backend
)


class TestLookupPointsEditor:
    """Test the Lookup Points Editor component."""
    
    def test_generate_year_range(self):
        """Test year range generation with different parameters."""
        # Test basic range
        years = _generate_year_range(2025.0, 2026.0, 0.25)
        expected = [2025.0, 2025.25, 2025.5, 2025.75, 2026.0]
        assert years == expected
        
        # Test with different dt
        years = _generate_year_range(2020.0, 2021.0, 0.5)
        expected = [2020.0, 2020.5, 2021.0]
        assert years == expected
    
    def test_initialize_lookup_points_state(self):
        """Test state initialization with default values."""
        state = LookupPointsState()
        products = ["Product_A", "Product_B"]
        years = [2025.0, 2025.25, 2025.5]
        
        _initialize_lookup_points_state(state, products, years)
        
        # Check production capacity
        assert "Product_A" in state.production_capacity
        assert "Product_B" in state.production_capacity
        assert 2025.0 in state.production_capacity["Product_A"]
        assert state.production_capacity["Product_A"][2025.0] > 0
        
        # Check pricing
        assert "Product_A" in state.pricing
        assert "Product_B" in state.pricing
        assert 2025.0 in state.pricing["Product_A"]
        assert state.pricing["Product_A"][2025.0] > 0
    
    def test_create_production_capacity_dataframe(self):
        """Test production capacity DataFrame creation."""
        state = LookupPointsState()
        products = ["Product_A", "Product_B"]
        years = [2025.0, 2025.25]
        
        # Initialize with some data
        _initialize_lookup_points_state(state, products, years)
        
        df = _create_production_capacity_dataframe(state, products, years)
        
        assert isinstance(df, pd.DataFrame)
        assert "Product" in df.columns
        assert "2025.0" in df.columns
        assert "2025.25" in df.columns
        assert len(df) == 2  # Two products
        assert df.iloc[0]["Product"] == "Product_A"
        assert df.iloc[1]["Product"] == "Product_B"
    
    def test_create_pricing_dataframe(self):
        """Test pricing DataFrame creation."""
        state = LookupPointsState()
        products = ["Product_A", "Product_B"]
        years = [2025.0, 2025.25]
        
        # Initialize with some data
        _initialize_lookup_points_state(state, products, years)
        
        df = _create_pricing_dataframe(state, products, years)
        
        assert isinstance(df, pd.DataFrame)
        assert "Product" in df.columns
        assert "2025.0" in df.columns
        assert "2025.25" in df.columns
        assert len(df) == 2  # Two products
        assert df.iloc[0]["Product"] == "Product_A"
        assert df.iloc[1]["Product"] == "Product_B"
    
    def test_get_lookup_points_for_yaml(self):
        """Test conversion to YAML-compatible format."""
        state = LookupPointsState()
        products = ["Product_A"]
        years = [2025.0, 2025.25]
        
        # Initialize with some data
        _initialize_lookup_points_state(state, products, years)
        
        yaml_data = get_lookup_points_for_yaml(state)
        
        assert "max_capacity_Product_A" in yaml_data
        assert "price_Product_A" in yaml_data
        assert len(yaml_data["max_capacity_Product_A"]) == 2
        assert len(yaml_data["price_Product_A"]) == 2
        
        # Check data format
        assert isinstance(yaml_data["max_capacity_Product_A"][0], list)
        assert len(yaml_data["max_capacity_Product_A"][0]) == 2
        assert yaml_data["max_capacity_Product_A"][0][0] == 2025.0


class TestRunnerTab:
    """Test the Runner Tab component."""
    
    def test_check_for_unsaved_changes(self):
        """Test unsaved changes detection."""
        state = RunnerState()
        
        # Initially no changes
        assert not _check_for_unsaved_changes(state)
        
        # Set unsaved changes
        state.has_unsaved_changes = True
        assert _check_for_unsaved_changes(state)
    
    def test_get_execution_config_for_backend(self):
        """Test conversion to backend-compatible configuration."""
        state = RunnerState()
        state.current_scenario = "test_scenario"
        state.debug_mode = True
        state.generate_plots = False
        state.kpi_sm_revenue_rows = True
        state.kpi_sm_client_rows = False
        
        config = get_execution_config_for_backend(state)
        
        assert config["scenario_name"] == "test_scenario"
        assert config["debug_mode"] is True
        assert config["generate_plots"] is False
        assert config["kpi_sm_revenue_rows"] is True
        assert config["kpi_sm_client_rows"] is False


class TestLogsTab:
    """Test the Logs Tab component."""
    
    def test_log_parsing_functionality(self):
        """Test log parsing functionality."""
        from ui.components.logs_tab import _parse_log_line, _should_include_log
        
        # Test log line parsing
        sample_log_line = "2025-08-27 01:51:17,158 | INFO | src.phase1_data | Loading Phase 1 inputs from JSON: inputs.json"
        parsed = _parse_log_line(sample_log_line)
        
        assert parsed is not None
        assert parsed["level"] == "INFO"
        assert parsed["source"] == "src.phase1_data"
        assert "Loading Phase 1 inputs" in parsed["message"]
        
        # Test log level filtering
        assert _should_include_log(parsed, "ALL") == True
        assert _should_include_log(parsed, "INFO") == True
        assert _should_include_log(parsed, "WARNING") == False
        assert _should_include_log(parsed, "ERROR") == False
    
    def test_log_level_filtering(self):
        """Test log level filtering functionality."""
        from ui.components.logs_tab import _should_include_log
        
        # Test different log levels
        error_log = {"level": "ERROR", "timestamp": None, "source": "", "message": ""}
        warning_log = {"level": "WARNING", "timestamp": None, "source": "", "message": ""}
        info_log = {"level": "INFO", "timestamp": None, "source": "", "message": ""}
        debug_log = {"level": "DEBUG", "timestamp": None, "source": "", "message": ""}
        
        # Test INFO level filtering
        assert _should_include_log(error_log, "INFO") == True
        assert _should_include_log(warning_log, "INFO") == True
        assert _should_include_log(info_log, "INFO") == True
        assert _should_include_log(debug_log, "INFO") == False
    
    def test_get_logs_config_for_backend(self):
        """Test conversion to backend-compatible configuration."""
        state = LogsState()
        state.log_level = "INFO"
        state.max_log_lines = 2000
        state.auto_refresh = True
        
        config = get_logs_config_for_backend(state)
        
        assert config["log_level"] == "INFO"
        assert config["max_log_lines"] == 2000
        assert config["auto_refresh"] is True


class TestIntegration:
    """Test integration between components."""
    
    def test_lookup_points_with_simulation_definitions(self):
        """Test lookup points integration with simulation definitions."""
        # Create simulation definitions
        sim_defs = SimulationDefinitionsState()
        sim_defs.products = ["Product_1", "Product_2"]
        
        # Create runspecs
        runspecs = RunspecsState()
        runspecs.starttime = 2025.0
        runspecs.stoptime = 2026.0
        runspecs.dt = 0.25
        
        # Create lookup points state
        lookup_state = LookupPointsState()
        
        # Generate years
        years = _generate_year_range(runspecs.starttime, runspecs.stoptime, runspecs.dt)
        assert len(years) == 5  # 2025.0, 2025.25, 2025.5, 2025.75, 2026.0
        
        # Initialize lookup points
        _initialize_lookup_points_state(lookup_state, sim_defs.products, years)
        
        # Verify data structure
        assert len(lookup_state.production_capacity) == 2
        assert len(lookup_state.pricing) == 2
        assert all(len(lookup_state.production_capacity[p]) == 5 for p in sim_defs.products)
        assert all(len(lookup_state.pricing[p]) == 5 for p in sim_defs.products)
    
    def test_state_consistency(self):
        """Test that state objects maintain consistency."""
        # Test LookupPointsState
        lookup_state = LookupPointsState()
        assert hasattr(lookup_state, 'production_capacity')
        assert hasattr(lookup_state, 'pricing')
        assert hasattr(lookup_state, 'has_unsaved_changes')
        
        # Test RunnerState
        runner_state = RunnerState()
        assert hasattr(runner_state, 'is_running')
        assert hasattr(runner_state, 'current_scenario')
        assert hasattr(runner_state, 'debug_mode')
        assert hasattr(runner_state, 'has_unsaved_changes')
        
        # Test LogsState
        logs_state = LogsState()
        assert hasattr(logs_state, 'log_level')
        assert hasattr(logs_state, 'max_log_lines')
        assert hasattr(logs_state, 'auto_refresh')
        assert hasattr(logs_state, 'has_unsaved_changes')


if __name__ == "__main__":
    pytest.main([__file__])
