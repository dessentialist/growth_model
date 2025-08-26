"""
Framework-agnostic scenario management for the Growth Model UI.

This module handles all scenario-related operations including loading, saving,
validation, and management of scenario files. It's completely independent of
any UI framework and provides pure business logic.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import yaml
import json

from .state_manager import StateManager

logger = logging.getLogger(__name__)


class ScenarioManager:
    """
    Framework-agnostic scenario management.
    
    This class handles all scenario operations including:
    - Loading scenarios from YAML/JSON files
    - Saving scenarios to files
    - Scenario validation
    - Scenario listing and discovery
    - Scenario duplication and management
    """
    
    def __init__(self, scenarios_dir: Path, state_manager: StateManager):
        """Initialize the scenario manager.
        
        Args:
            scenarios_dir: Directory containing scenario files
            state_manager: State manager instance for state operations
        """
        self.scenarios_dir = Path(scenarios_dir)
        self.state_manager = state_manager
        self.scenarios_dir.mkdir(exist_ok=True)
        
    def list_available_scenarios(self) -> List[Path]:
        """List all available scenario files.
        
        Returns:
            List of Path objects for scenario files
        """
        try:
            scenario_files = []
            for file_path in self.scenarios_dir.glob("*.yaml"):
                scenario_files.append(file_path)
            for file_path in self.scenarios_dir.glob("*.yml"):
                scenario_files.append(file_path)
            for file_path in self.scenarios_dir.glob("*.json"):
                scenario_files.append(file_path)
            return sorted(scenario_files)
        except Exception as e:
            logger.error(f"Error listing scenarios: {e}")
            return []
    
    def load_scenario(self, scenario_name: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Load a scenario by name.
        
        Args:
            scenario_name: Name of the scenario file (with or without extension)
            
        Returns:
            Tuple of (success, error_message, scenario_data)
        """
        try:
            # Try different extensions
            for ext in [".yaml", ".yml", ".json"]:
                file_path = self.scenarios_dir / f"{scenario_name}{ext}"
                if file_path.exists():
                    return self._load_scenario_file(file_path)
            
            # If no extension provided, try with .yaml
            file_path = self.scenarios_dir / f"{scenario_name}.yaml"
            if file_path.exists():
                return self._load_scenario_file(file_path)
            
            return False, f"Scenario '{scenario_name}' not found", None
            
        except Exception as e:
            error_msg = f"Error loading scenario '{scenario_name}': {e}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def _load_scenario_file(self, file_path: Path) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Load a scenario from a specific file.
        
        Args:
            file_path: Path to the scenario file
            
        Returns:
            Tuple of (success, error_message, scenario_data)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    return False, f"Unsupported file format: {file_path.suffix}", None
                
                if not isinstance(data, dict):
                    return False, "Invalid scenario file: root must be a dictionary", None
                
                return True, None, data
                
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error in {file_path}: {e}"
            logger.error(error_msg)
            return False, error_msg, None
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error in {file_path}: {e}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Error reading {file_path}: {e}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def save_scenario(
        self, 
        scenario_data: Dict, 
        filename: str, 
        overwrite: bool = False
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        """Save a scenario to a file.
        
        Args:
            scenario_data: Scenario data dictionary
            filename: Name of the file to save (with or without extension)
            overwrite: Whether to overwrite existing files
            
        Returns:
            Tuple of (success, error_message, file_path)
        """
        try:
            # Ensure filename has .yaml extension
            if not filename.endswith(('.yaml', '.yml', '.json')):
                filename = f"{filename}.yaml"
            
            file_path = self.scenarios_dir / filename
            
            # Check if file exists and overwrite is not allowed
            if file_path.exists() and not overwrite:
                return False, f"File {filename} already exists. Use overwrite=True to overwrite.", None
            
            # Save the file
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(scenario_data, f, default_flow_style=False, sort_keys=False)
                elif file_path.suffix.lower() == '.json':
                    json.dump(scenario_data, f, indent=2, sort_keys=False)
                else:
                    return False, f"Unsupported file format: {file_path.suffix}", None
            
            logger.info(f"Scenario saved to {file_path}")
            return True, None, file_path
            
        except Exception as e:
            error_msg = f"Error saving scenario to {filename}: {e}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def duplicate_scenario(self, source_name: str, new_name: str) -> Tuple[bool, Optional[str], Optional[Path]]:
        """Duplicate an existing scenario.
        
        Args:
            source_name: Name of the source scenario
            new_name: Name for the new scenario
            
        Returns:
            Tuple of (success, error_message, file_path)
        """
        try:
            # Load the source scenario
            success, error, data = self.load_scenario(source_name)
            if not success:
                return False, error, None
            
            # Update the name in the data
            data['name'] = new_name
            
            # Save as new scenario
            return self.save_scenario(data, new_name, overwrite=False)
            
        except Exception as e:
            error_msg = f"Error duplicating scenario {source_name} to {new_name}: {e}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def delete_scenario(self, scenario_name: str) -> Tuple[bool, Optional[str]]:
        """Delete a scenario file.
        
        Args:
            scenario_name: Name of the scenario to delete
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Try different extensions
            for ext in [".yaml", ".yml", ".json"]:
                file_path = self.scenarios_dir / f"{scenario_name}{ext}"
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted scenario {file_path}")
                    return True, None
            
            # If no extension provided, try with .yaml
            file_path = self.scenarios_dir / f"{scenario_name}.yaml"
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted scenario {file_path}")
                return True, None
            
            return False, f"Scenario '{scenario_name}' not found"
            
        except Exception as e:
            error_msg = f"Error deleting scenario '{scenario_name}': {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def load_scenario_into_state(self, scenario_name: str) -> Tuple[bool, Optional[str]]:
        """Load a scenario and update the state manager.
        
        Args:
            scenario_name: Name of the scenario to load
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            success, error, data = self.load_scenario(scenario_name)
            if not success:
                return False, error
            
            # Load the data into the state manager
            self.state_manager.load_from_scenario_dict(data)
            logger.info(f"Loaded scenario '{scenario_name}' into state")
            return True, None
            
        except Exception as e:
            error_msg = f"Error loading scenario '{scenario_name}' into state: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def save_current_state_as_scenario(
        self, 
        filename: str, 
        overwrite: bool = False
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        """Save the current state as a scenario file.
        
        Args:
            filename: Name of the file to save
            overwrite: Whether to overwrite existing files
            
        Returns:
            Tuple of (success, error_message, file_path)
        """
        try:
            # Get the current state as scenario data
            scenario_data = self.state_manager.to_scenario_dict_normalized()
            
            # Save the scenario
            return self.save_scenario(scenario_data, filename, overwrite)
            
        except Exception as e:
            error_msg = f"Error saving current state as scenario: {e}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def get_scenario_info(self, scenario_name: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Get information about a scenario without loading it into state.
        
        Args:
            scenario_name: Name of the scenario
            
        Returns:
            Tuple of (success, error_message, scenario_info)
        """
        try:
            success, error, data = self.load_scenario(scenario_name)
            if not success:
                return False, error, None
            
            # Extract basic information
            info = {
                'name': data.get('name', scenario_name),
                'runspecs': data.get('runspecs', {}),
                'has_constants': bool(data.get('overrides', {}).get('constants')),
                'has_points': bool(data.get('overrides', {}).get('points')),
                'has_primary_map': bool(data.get('overrides', {}).get('primary_map')),
                'has_seeds': bool(data.get('seeds')),
                'constants_count': len(data.get('overrides', {}).get('constants', {})),
                'points_count': len(data.get('overrides', {}).get('points', {})),
            }
            
            return True, None, info
            
        except Exception as e:
            error_msg = f"Error getting info for scenario '{scenario_name}': {e}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def validate_scenario_data(self, scenario_data: Dict) -> Tuple[bool, Optional[str]]:
        """Validate scenario data structure.
        
        Args:
            scenario_data: Scenario data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not isinstance(scenario_data, dict):
                return False, "Scenario data must be a dictionary"
            
            # Check required fields
            if 'name' not in scenario_data:
                return False, "Scenario must have a 'name' field"
            
            if not isinstance(scenario_data['name'], str):
                return False, "Scenario name must be a string"
            
            # Check runspecs
            runspecs = scenario_data.get('runspecs', {})
            if not isinstance(runspecs, dict):
                return False, "Runspecs must be a dictionary"
            
            # Validate runspecs fields if present
            for field in ['starttime', 'stoptime', 'dt']:
                if field in runspecs:
                    try:
                        float(runspecs[field])
                    except (ValueError, TypeError):
                        return False, f"Runspecs field '{field}' must be a number"
            
            # Check overrides
            overrides = scenario_data.get('overrides', {})
            if not isinstance(overrides, dict):
                return False, "Overrides must be a dictionary"
            
            # Validate constants
            constants = overrides.get('constants', {})
            if not isinstance(constants, dict):
                return False, "Constants must be a dictionary"
            
            for key, value in constants.items():
                if not isinstance(key, str):
                    return False, "Constant keys must be strings"
                try:
                    float(value)
                except (ValueError, TypeError):
                    return False, f"Constant value for '{key}' must be a number"
            
            # Validate points
            points = overrides.get('points', {})
            if not isinstance(points, dict):
                return False, "Points must be a dictionary"
            
            for key, series in points.items():
                if not isinstance(key, str):
                    return False, "Point keys must be strings"
                if not isinstance(series, list):
                    return False, f"Point series for '{key}' must be a list"
                
                for i, point in enumerate(series):
                    if not isinstance(point, (list, tuple)) or len(point) != 2:
                        return False, f"Point {i} in series '{key}' must be a list/tuple of 2 numbers"
                    try:
                        float(point[0])
                        float(point[1])
                    except (ValueError, TypeError):
                        return False, f"Point {i} in series '{key}' must contain numbers"
            
            # Validate seeds
            seeds = scenario_data.get('seeds', {})
            if not isinstance(seeds, dict):
                return False, "Seeds must be a dictionary"
            
            # Validate seed fields
            for seed_type in ['active_anchor_clients', 'elapsed_quarters', 'direct_clients', 'completed_projects']:
                if seed_type in seeds:
                    seed_data = seeds[seed_type]
                    if not isinstance(seed_data, dict):
                        return False, f"Seed field '{seed_type}' must be a dictionary"
                    for key, value in seed_data.items():
                        if not isinstance(key, str):
                            return False, f"Seed keys in '{seed_type}' must be strings"
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            return False, f"Seed value for '{key}' in '{seed_type}' must be an integer"
            
            # Validate SM-mode seeds
            for seed_type in ['active_anchor_clients_sm', 'completed_projects_sm']:
                if seed_type in seeds:
                    seed_data = seeds[seed_type]
                    if not isinstance(seed_data, dict):
                        return False, f"Seed field '{seed_type}' must be a dictionary"
                    for sector, products in seed_data.items():
                        if not isinstance(sector, str):
                            return False, f"Seed sector keys in '{seed_type}' must be strings"
                        if not isinstance(products, dict):
                            return False, f"Seed products for sector '{sector}' in '{seed_type}' must be a dictionary"
                        for product, value in products.items():
                            if not isinstance(product, str):
                                return False, f"Seed product keys in '{seed_type}' must be strings"
                            try:
                                int(value)
                            except (ValueError, TypeError):
                                return False, f"Seed value for '{product}' in '{seed_type}' must be an integer"
            
            return True, None
            
        except Exception as e:
            error_msg = f"Error validating scenario data: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_scenario_summary(self) -> Dict[str, Any]:
        """Get a summary of all available scenarios.
        
        Returns:
            Dictionary with scenario summary information
        """
        try:
            scenarios = self.list_available_scenarios()
            summary = {
                'total_scenarios': len(scenarios),
                'scenarios': []
            }
            
            for scenario_path in scenarios:
                success, error, info = self.get_scenario_info(scenario_path.stem)
                if success and info:
                    summary['scenarios'].append({
                        'name': scenario_path.stem,
                        'path': str(scenario_path),
                        'info': info
                    })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting scenario summary: {e}")
            return {'total_scenarios': 0, 'scenarios': []}
