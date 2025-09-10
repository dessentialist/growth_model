"""
Tests for Phase 1 UI Logic Implementation.

This test suite verifies the framework-agnostic business logic components
including state management, validation, scenario management, and data management.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from src.ui_logic import (
    StateManager, ScenarioManager, ValidationManager, RunnerManager, DataManager
)
from src.ui_logic.state_manager import (
    UIState, RunspecsState, ScenarioOverridesState, PrimaryMapState, SeedsState,
    RunnerState, LogsState, OutputState, TabType
)
from src.ui_logic.validation_manager import ValidationError, ValidationResult
from src.ui_logic.data_manager import DataBundle, PermissibleKeys


class TestStateManager:
    """Test the StateManager class."""
    
    def test_initialization(self):
        """Test StateManager initialization."""
        manager = StateManager()
        state = manager.get_state()
        
        assert isinstance(state, UIState)
        assert state.name == "working_scenario"
        assert state.active_tab == TabType.RUNNER
        assert isinstance(state.runspecs, RunspecsState)
        assert isinstance(state.overrides, ScenarioOverridesState)
        assert isinstance(state.primary_map, PrimaryMapState)
        assert isinstance(state.seeds, SeedsState)
        assert isinstance(state.runner, RunnerState)
        assert isinstance(state.logs, LogsState)
        assert isinstance(state.output, OutputState)
    
    def test_update_runspecs(self):
        """Test updating runspecs."""
        manager = StateManager()
        
        # Update runspecs
        manager.update_runspecs(
            starttime=2026.0,
            stoptime=2035.0,
            dt=0.5,
            anchor_mode="sm"
        )
        
        state = manager.get_state()
        assert state.runspecs.starttime == 2026.0
        assert state.runspecs.stoptime == 2035.0
        assert state.runspecs.dt == 0.5
        assert state.runspecs.anchor_mode == "sm"
    
    def test_update_overrides(self):
        """Test updating overrides."""
        manager = StateManager()
        
        # Update constants
        constants = {"test_param": 42.0}
        manager.update_overrides(constants=constants)
        
        state = manager.get_state()
        assert state.overrides.constants == constants
    
    def test_set_active_tab(self):
        """Test setting active tab."""
        manager = StateManager()
        
        manager.set_active_tab(TabType.PARAMETERS)
        state = manager.get_state()
        assert state.active_tab == TabType.PARAMETERS
    
    def test_to_scenario_dict(self):
        """Test converting state to scenario dictionary."""
        manager = StateManager()
        
        # Set some test data
        manager.update_runspecs(starttime=2025.0, stoptime=2030.0)
        manager.update_overrides(constants={"test_param": 42.0})
        
        scenario_dict = manager.to_scenario_dict()
        
        assert scenario_dict["name"] == "working_scenario"
        assert scenario_dict["runspecs"]["starttime"] == 2025.0
        assert scenario_dict["runspecs"]["stoptime"] == 2030.0
        assert scenario_dict["overrides"]["constants"]["test_param"] == 42.0
    
    def test_load_from_scenario_dict(self):
        """Test loading state from scenario dictionary."""
        manager = StateManager()
        
        scenario_data = {
            "name": "test_scenario",
            "runspecs": {
                "starttime": 2025.0,
                "stoptime": 2030.0,
                "dt": 0.25,
                "anchor_mode": "sector"
            },
            "overrides": {
                "constants": {"test_param": 42.0},
                "points": {"test_series": [[2025.0, 10.0], [2026.0, 20.0]]}
            }
        }
        
        manager.load_from_scenario_dict(scenario_data)
        state = manager.get_state()
        
        assert state.name == "test_scenario"
        assert state.runspecs.starttime == 2025.0
        assert state.runspecs.stoptime == 2030.0
        assert state.overrides.constants["test_param"] == 42.0
        assert len(state.overrides.points["test_series"]) == 2


class TestValidationManager:
    """Test the ValidationManager class."""
    
    def test_initialization(self):
        """Test ValidationManager initialization."""
        state_manager = Mock()
        data_manager = Mock()
        manager = ValidationManager(state_manager, data_manager)
        
        assert manager.state_manager == state_manager
        assert manager.data_manager == data_manager
    
    def test_validate_runspecs_valid(self):
        """Test validating valid runspecs."""
        manager = ValidationManager(Mock(), Mock())
        
        runspecs = {
            "starttime": 2025.0,
            "stoptime": 2030.0,
            "dt": 0.25,
            "anchor_mode": "sector"
        }
        
        result = manager.validate_runspecs(runspecs)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_runspecs_invalid(self):
        """Test validating invalid runspecs."""
        manager = ValidationManager(Mock(), Mock())
        
        runspecs = {
            "starttime": -1.0,  # Invalid: negative
            "stoptime": 2025.0,  # Invalid: less than starttime
            "dt": 0.0,  # Invalid: zero
            "anchor_mode": "invalid"  # Invalid: not sector or sm
        }
        
        result = manager.validate_runspecs(runspecs)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validate_constants(self):
        """Test validating constants."""
        manager = ValidationManager(Mock(), Mock())
        
        constants = {
            "valid_param": 42.0,
            "negative_param": -1.0,
            "invalid_type": "not_a_number"
        }
        
        permissible_keys = {"valid_param", "negative_param", "invalid_type"}
        
        result = manager.validate_constants(constants, permissible_keys)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validate_points(self):
        """Test validating points."""
        manager = ValidationManager(Mock(), Mock())
        
        points = {
            "valid_series": [[2025.0, 10.0], [2026.0, 20.0]],
            "unsorted_series": [[2026.0, 20.0], [2025.0, 10.0]],
            "invalid_point": [[2025.0, "not_a_number"]]
        }
        
        result = manager.validate_points(points)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validation_error(self):
        """Test ValidationError class."""
        error = ValidationError(
            field="test_field",
            message="Test error message",
            severity="error",
            context={"key": "value"}
        )
        
        assert error.field == "test_field"
        assert error.message == "Test error message"
        assert error.severity == "error"
        assert error.context["key"] == "value"
        
        # Test string representation
        assert str(error) == "test_field: Test error message"
        
        # Test dictionary representation
        error_dict = error.to_dict()
        assert error_dict["field"] == "test_field"
        assert error_dict["message"] == "Test error message"
        assert error_dict["severity"] == "error"
        assert error_dict["context"]["key"] == "value"


class TestScenarioManager:
    """Test the ScenarioManager class."""
    
    def test_initialization(self, tmp_path):
        """Test ScenarioManager initialization."""
        scenarios_dir = tmp_path / "scenarios"
        state_manager = Mock()
        manager = ScenarioManager(scenarios_dir, state_manager)
        
        assert manager.scenarios_dir == scenarios_dir
        assert manager.state_manager == state_manager
        assert scenarios_dir.exists()
    
    def test_list_available_scenarios_empty(self, tmp_path):
        """Test listing scenarios when directory is empty."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        manager = ScenarioManager(scenarios_dir, Mock())
        scenarios = manager.list_available_scenarios()
        
        assert len(scenarios) == 0
    
    def test_save_and_load_scenario(self, tmp_path):
        """Test saving and loading a scenario."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        manager = ScenarioManager(scenarios_dir, Mock())
        
        # Test scenario data
        scenario_data = {
            "name": "test_scenario",
            "runspecs": {
                "starttime": 2025.0,
                "stoptime": 2030.0,
                "dt": 0.25
            },
            "overrides": {
                "constants": {"test_param": 42.0}
            }
        }
        
        # Save scenario
        success, error, path = manager.save_scenario(scenario_data, "test_scenario.yaml")
        assert success
        assert path is not None
        assert path.exists()
        
        # Load scenario
        success, error, loaded_data = manager.load_scenario("test_scenario")
        assert success
        assert loaded_data is not None
        assert loaded_data["name"] == "test_scenario"
        assert loaded_data["runspecs"]["starttime"] == 2025.0
    
    def test_duplicate_scenario(self, tmp_path):
        """Test duplicating a scenario."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        manager = ScenarioManager(scenarios_dir, Mock())
        
        # Create original scenario
        original_data = {"name": "original", "runspecs": {"starttime": 2025.0}}
        manager.save_scenario(original_data, "original.yaml")
        
        # Duplicate scenario
        success, error, path = manager.duplicate_scenario("original", "duplicate")
        assert success
        assert path is not None
        
        # Verify duplicate
        success, error, duplicate_data = manager.load_scenario("duplicate")
        assert success
        assert duplicate_data["name"] == "duplicate"
    
    def test_validate_scenario_data(self, tmp_path):
        """Test scenario data validation."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        manager = ScenarioManager(scenarios_dir, Mock())
        
        # Valid scenario
        valid_scenario = {
            "name": "test",
            "runspecs": {"starttime": 2025.0, "stoptime": 2030.0},
            "overrides": {
                "constants": {"param": 42.0},
                "points": {"series": [[2025.0, 10.0]]}
            }
        }
        
        success, error = manager.validate_scenario_data(valid_scenario)
        assert success
        assert error is None
        
        # Invalid scenario
        invalid_scenario = {
            "runspecs": "not_a_dict"
        }
        
        success, error = manager.validate_scenario_data(invalid_scenario)
        assert not success
        assert error is not None


class TestDataManager:
    """Test the DataManager class."""
    
    def test_initialization(self, tmp_path):
        """Test DataManager initialization."""
        state_manager = Mock()
        project_root = tmp_path
        
        manager = DataManager(state_manager, project_root)
        
        assert manager.state_manager == state_manager
        assert manager.project_root == project_root
        assert manager._data_bundle is None
    
    def test_load_data_bundle_missing_file(self, tmp_path):
        """Test loading data bundle when inputs.json is missing."""
        state_manager = Mock()
        manager = DataManager(state_manager, tmp_path)
        
        success, error, bundle = manager.load_data_bundle()
        assert not success
        assert "inputs.json not found" in error
        assert bundle is None
    
    def test_load_data_bundle_invalid_json(self, tmp_path):
        """Test loading data bundle with invalid JSON."""
        state_manager = Mock()
        manager = DataManager(state_manager, tmp_path)
        
        # Create invalid JSON file
        inputs_file = tmp_path / "inputs.json"
        inputs_file.write_text("invalid json content")
        
        success, error, bundle = manager.load_data_bundle()
        assert not success
        assert "Error parsing inputs.json" in error
        assert bundle is None
    
    def test_load_data_bundle_valid(self, tmp_path):
        """Test loading valid data bundle."""
        state_manager = Mock()
        manager = DataManager(state_manager, tmp_path)
        
        # Create valid inputs.json
        inputs_data = {
            "lists": {
                "lists": {
                    "markets": ["US"],
                    "sectors": ["Defense", "Aviation"],
                    "products": ["Product1", "Product2"]
                }
            },
            "anchor_params": {
                "Defense": {"param1": 1.0},
                "Aviation": {"param2": 2.0}
            },
            "other_params": {
                "Product1": {"param3": 3.0},
                "Product2": {"param4": 4.0}
            },
            "production": {
                "Product1": {"2025": 10.0},
                "Product2": {"2025": 20.0}
            },
            "pricing": {
                "Product1": {"2025": 100.0},
                "Product2": {"2025": 200.0}
            },
            "primary_map": {
                "Defense": [
                    {"product": "Product1", "start_year": 2025.0}
                ],
                "Aviation": [
                    {"product": "Product2", "start_year": 2026.0}
                ]
            }
        }
        
        inputs_file = tmp_path / "inputs.json"
        inputs_file.write_text(json.dumps(inputs_data))
        
        success, error, bundle = manager.load_data_bundle()
        assert success
        assert error is None
        assert bundle is not None
        assert isinstance(bundle, DataBundle)
    
    def test_get_permissible_keys(self, tmp_path):
        """Test getting permissible keys."""
        state_manager = Mock()
        manager = DataManager(state_manager, tmp_path)
        
        # Create minimal valid inputs.json
        inputs_data = {
            "lists": {
                "lists": {
                    "markets": ["US"],
                    "sectors": ["Defense"],
                    "products": ["Product1"]
                }
            },
            "anchor_params": {"Defense": {}},
            "other_params": {"Product1": {}},
            "production": {"Product1": {"2025": 10.0}},
            "pricing": {"Product1": {"2025": 100.0}},
            "primary_map": {"Defense": [{"product": "Product1", "start_year": 2025.0}]}
        }
        
        inputs_file = tmp_path / "inputs.json"
        inputs_file.write_text(json.dumps(inputs_data))
        
        # Test sector mode
        keys = manager.get_permissible_keys("sector")
        assert isinstance(keys, PermissibleKeys)
        assert "anchor_start_year_Defense" in keys.constants
        assert "price_Product1" in keys.points
        assert "Defense" in keys.sectors
        assert "Product1" in keys.products
    
    def test_get_available_sectors_and_products(self, tmp_path):
        """Test getting available sectors and products."""
        state_manager = Mock()
        manager = DataManager(state_manager, tmp_path)
        
        # Create inputs.json with sectors and products
        inputs_data = {
            "lists": {
                "lists": {
                    "markets": ["US"],
                    "sectors": ["Defense", "Aviation"],
                    "products": ["Product1", "Product2"]
                }
            },
            "anchor_params": {"Defense": {}, "Aviation": {}},
            "other_params": {"Product1": {}, "Product2": {}},
            "production": {"Product1": {"2025": 10.0}, "Product2": {"2025": 20.0}},
            "pricing": {"Product1": {"2025": 100.0}, "Product2": {"2025": 200.0}},
            "primary_map": {"Defense": [{"product": "Product1", "start_year": 2025.0}]}
        }
        
        inputs_file = tmp_path / "inputs.json"
        inputs_file.write_text(json.dumps(inputs_data))
        
        sectors = manager.get_available_sectors()
        products = manager.get_available_products()
        
        assert sectors == ["Defense", "Aviation"]
        assert products == ["Product1", "Product2"]


class TestRunnerManager:
    """Test the RunnerManager class."""
    
    def test_initialization(self, tmp_path):
        """Test RunnerManager initialization."""
        state_manager = Mock()
        project_root = tmp_path
        
        manager = RunnerManager(state_manager, project_root)
        
        assert manager.state_manager == state_manager
        assert manager.project_root == project_root
        assert manager.current_process is None
    
    def test_build_runner_command_preset(self, tmp_path):
        """Test building runner command with preset."""
        state_manager = Mock()
        manager = RunnerManager(state_manager, tmp_path)
        
        command = manager.build_runner_command(
            preset="baseline",
            debug=True,
            visualize=False
        )
        
        assert isinstance(command.command, list)
        assert "python" in command.command[0]
        assert "simulate_growth.py" in command.command[1]
        assert "--preset" in command.command
        assert "baseline" in command.command
        assert "--debug" in command.command
    
    def test_build_runner_command_scenario_path(self, tmp_path):
        """Test building runner command with scenario path."""
        state_manager = Mock()
        manager = RunnerManager(state_manager, tmp_path)
        
        scenario_path = tmp_path / "test_scenario.yaml"
        command = manager.build_runner_command(
            scenario_path=scenario_path,
            debug=False,
            visualize=True
        )
        
        assert "--scenario" in command.command
        assert str(scenario_path) in command.command
        assert "--visualize" in command.command
    
    def test_get_simulation_status(self, tmp_path):
        """Test getting simulation status."""
        state_manager = Mock()
        manager = RunnerManager(state_manager, tmp_path)
        
        status = manager.get_simulation_status()
        assert isinstance(status, manager.current_status.__class__)
        assert not status.is_running
        assert status.exit_code is None
    
    def test_get_latest_results_no_results(self, tmp_path):
        """Test getting latest results when none exist."""
        state_manager = Mock()
        manager = RunnerManager(state_manager, tmp_path)
        
        results_path = manager.get_latest_results()
        assert results_path is None
    
    def test_get_latest_plots_no_plots(self, tmp_path):
        """Test getting latest plots when none exist."""
        state_manager = Mock()
        manager = RunnerManager(state_manager, tmp_path)
        
        plots = manager.get_latest_plots()
        assert plots == []


class TestIntegration:
    """Integration tests for the UI logic components."""
    
    def test_state_manager_with_validation(self, tmp_path):
        """Test StateManager integration with ValidationManager."""
        # Create valid inputs.json
        inputs_data = {
            "lists": {
                "lists": {
                    "markets": ["US"],
                    "sectors": ["Defense"],
                    "products": ["Product1"]
                }
            },
            "anchor_params": {"Defense": {}},
            "other_params": {"Product1": {}},
            "production": {"Product1": {"2025": 10.0}},
            "pricing": {"Product1": {"2025": 100.0}},
            "primary_map": {"Defense": [{"product": "Product1", "start_year": 2025.0}]}
        }
        
        inputs_file = tmp_path / "inputs.json"
        inputs_file.write_text(json.dumps(inputs_data))
        
        # Initialize managers
        state_manager = StateManager()
        data_manager = DataManager(state_manager, tmp_path)
        validation_manager = ValidationManager(state_manager, data_manager)
        
        # Load data
        success, error, bundle = data_manager.load_data_bundle()
        assert success
        
        # Update state with valid data
        state_manager.update_runspecs(starttime=2025.0, stoptime=2030.0)
        state_manager.update_overrides(constants={"anchor_start_year_Defense": 2025.0})
        
        # Validate state
        permissible_keys = data_manager.get_permissible_keys("sector")
        validation_result = validation_manager.validate_current_state({
            'constants': permissible_keys.constants,
            'points': permissible_keys.points,
            'sectors': permissible_keys.sectors,
            'products': permissible_keys.products
        })
        
        assert validation_result.is_valid
    
    def test_scenario_manager_with_state_manager(self, tmp_path):
        """Test ScenarioManager integration with StateManager."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        state_manager = StateManager()
        scenario_manager = ScenarioManager(scenarios_dir, state_manager)
        
        # Update state
        state_manager.update_runspecs(starttime=2025.0, stoptime=2030.0)
        state_manager.update_overrides(constants={"test_param": 42.0})
        
        # Save state as scenario
        success, error, path = scenario_manager.save_current_state_as_scenario("test_scenario")
        assert success
        assert path.exists()
        
        # Load scenario into state
        success, error = scenario_manager.load_scenario_into_state("test_scenario")
        assert success
        
        # Verify state was updated
        state = state_manager.get_state()
        assert state.runspecs.starttime == 2025.0
        assert state.overrides.constants["test_param"] == 42.0


if __name__ == "__main__":
    pytest.main([__file__])
