"""
Framework-agnostic validation management for the Growth Model UI.

This module handles all validation logic including scenario validation,
parameter validation, and data validation. It's completely independent of
any UI framework and provides pure business logic.
"""

from typing import Dict, List, Optional, Any, Set
import logging

from .state_manager import StateManager

logger = logging.getLogger(__name__)


class ValidationError:
    """Represents a validation error with context."""
    
    def __init__(self, field: str, message: str, severity: str = "error", context: Optional[Dict] = None):
        """Initialize a validation error.
        
        Args:
            field: The field that failed validation
            message: Error message
            severity: Error severity (error, warning, info)
            context: Additional context information
        """
        self.field = field
        self.message = message
        self.severity = severity
        self.context = context or {}
    
    def __str__(self) -> str:
        return f"{self.field}: {self.message}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'field': self.field,
            'message': self.message,
            'severity': self.severity,
            'context': self.context
        }


class ValidationResult:
    """Represents the result of a validation operation."""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[ValidationError]] = None):
        """Initialize a validation result.
        
        Args:
            is_valid: Whether the validation passed
            errors: List of validation errors
        """
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, error: ValidationError) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_errors(self, errors: List[ValidationError]) -> None:
        """Add multiple errors to the result."""
        self.errors.extend(errors)
        if errors:
            self.is_valid = False
    
    def get_errors_by_severity(self, severity: str) -> List[ValidationError]:
        """Get errors filtered by severity."""
        return [error for error in self.errors if error.severity == severity]
    
    def get_errors_by_field(self, field: str) -> List[ValidationError]:
        """Get errors filtered by field."""
        return [error for error in self.errors if error.field == field]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'is_valid': self.is_valid,
            'errors': [error.to_dict() for error in self.errors],
            'error_count': len(self.get_errors_by_severity('error')),
            'warning_count': len(self.get_errors_by_severity('warning')),
            'info_count': len(self.get_errors_by_severity('info'))
        }


class ValidationManager:
    """
    Framework-agnostic validation management.
    
    This class handles all validation operations including:
    - Scenario validation
    - Parameter validation
    - Data validation
    - Real-time validation feedback
    """
    
    def __init__(self, state_manager: StateManager, data_manager: Any = None):
        """Initialize the validation manager.
        
        Args:
            state_manager: State manager instance
            data_manager: Data manager instance for data validation
        """
        self.state_manager = state_manager
        self.data_manager = data_manager
        self._validation_cache: Dict[str, ValidationResult] = {}
        
    def validate_runspecs(self, runspecs: Dict) -> ValidationResult:
        """Validate runspecs configuration.
        
        Args:
            runspecs: Runspecs dictionary to validate
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult()
        
        try:
            # Validate starttime
            if 'starttime' in runspecs:
                starttime = runspecs['starttime']
                try:
                    starttime_val = float(starttime)
                    if starttime_val < 0:
                        result.add_error(ValidationError(
                            'starttime', 
                            'Start time must be non-negative',
                            context={'value': starttime_val}
                        ))
                except (ValueError, TypeError):
                    result.add_error(ValidationError(
                        'starttime', 
                        'Start time must be a valid number',
                        context={'value': starttime}
                    ))
            
            # Validate stoptime
            if 'stoptime' in runspecs:
                stoptime = runspecs['stoptime']
                try:
                    stoptime_val = float(stoptime)
                    if stoptime_val < 0:
                        result.add_error(ValidationError(
                            'stoptime', 
                            'Stop time must be non-negative',
                            context={'value': stoptime_val}
                        ))
                except (ValueError, TypeError):
                    result.add_error(ValidationError(
                        'stoptime', 
                        'Stop time must be a valid number',
                        context={'value': stoptime}
                    ))
            
            # Validate dt
            if 'dt' in runspecs:
                dt = runspecs['dt']
                try:
                    dt_val = float(dt)
                    if dt_val <= 0:
                        result.add_error(ValidationError(
                            'dt', 
                            'Time step (dt) must be positive',
                            context={'value': dt_val}
                        ))
                    if dt_val > 1.0:
                        result.add_error(ValidationError(
                            'dt', 
                            'Time step (dt) should typically be 0.25 or less for quarterly simulation',
                            severity='warning',
                            context={'value': dt_val}
                        ))
                except (ValueError, TypeError):
                    result.add_error(ValidationError(
                        'dt', 
                        'Time step (dt) must be a valid number',
                        context={'value': dt}
                    ))
            
            # Validate anchor_mode
            if 'anchor_mode' in runspecs:
                anchor_mode = runspecs['anchor_mode']
                if not isinstance(anchor_mode, str):
                    result.add_error(ValidationError(
                        'anchor_mode', 
                        'Anchor mode must be a string',
                        context={'value': anchor_mode}
                    ))
                elif anchor_mode.lower() not in ['sector', 'sm']:
                    result.add_error(ValidationError(
                        'anchor_mode', 
                        'Anchor mode must be either "sector" or "sm"',
                        context={'value': anchor_mode}
                    ))
            
            # Validate time range
            if 'starttime' in runspecs and 'stoptime' in runspecs:
                try:
                    starttime_val = float(runspecs['starttime'])
                    stoptime_val = float(runspecs['stoptime'])
                    if stoptime_val <= starttime_val:
                        result.add_error(ValidationError(
                            'time_range', 
                            'Stop time must be greater than start time',
                            context={'starttime': starttime_val, 'stoptime': stoptime_val}
                        ))
                except (ValueError, TypeError):
                    pass  # Individual field errors already handled above
            
        except Exception as e:
            result.add_error(ValidationError(
                'runspecs', 
                f'Unexpected error validating runspecs: {e}',
                context={'exception': str(e)}
            ))
        
        return result
    
    def validate_constants(self, constants: Dict, permissible_keys: Optional[Set[str]] = None) -> ValidationResult:
        """Validate constants overrides.
        
        Args:
            constants: Constants dictionary to validate
            permissible_keys: Set of permissible constant keys
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult()
        
        try:
            if not isinstance(constants, dict):
                result.add_error(ValidationError(
                    'constants', 
                    'Constants must be a dictionary',
                    context={'type': type(constants).__name__}
                ))
                return result
            
            for key, value in constants.items():
                # Validate key format
                if not isinstance(key, str):
                    result.add_error(ValidationError(
                        f'constants.{key}', 
                        'Constant key must be a string',
                        context={'key': key, 'key_type': type(key).__name__}
                    ))
                    continue
                
                # Check if key is permissible
                if permissible_keys and key not in permissible_keys:
                    # Find similar keys for suggestion
                    suggestions = self._find_similar_keys(key, permissible_keys)
                    suggestion_msg = f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
                    result.add_error(ValidationError(
                        f'constants.{key}', 
                        f'Unknown constant key "{key}"{suggestion_msg}',
                        context={'key': key, 'suggestions': suggestions}
                    ))
                    continue
                
                # Validate value
                try:
                    float_val = float(value)
                    if float_val < 0 and self._is_negative_invalid(key):
                        result.add_error(ValidationError(
                            f'constants.{key}', 
                            f'Constant "{key}" cannot be negative',
                            context={'key': key, 'value': float_val}
                        ))
                except (ValueError, TypeError):
                    result.add_error(ValidationError(
                        f'constants.{key}', 
                        f'Constant "{key}" must be a valid number',
                        context={'key': key, 'value': value}
                    ))
            
        except Exception as e:
            result.add_error(ValidationError(
                'constants', 
                f'Unexpected error validating constants: {e}',
                context={'exception': str(e)}
            ))
        
        return result
    
    def validate_points(self, points: Dict, permissible_keys: Optional[Set[str]] = None) -> ValidationResult:
        """Validate points (time series) overrides.
        
        Args:
            points: Points dictionary to validate
            permissible_keys: Set of permissible point keys
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult()
        
        try:
            if not isinstance(points, dict):
                result.add_error(ValidationError(
                    'points', 
                    'Points must be a dictionary',
                    context={'type': type(points).__name__}
                ))
                return result
            
            for key, series in points.items():
                # Validate key format
                if not isinstance(key, str):
                    result.add_error(ValidationError(
                        f'points.{key}', 
                        'Point key must be a string',
                        context={'key': key, 'key_type': type(key).__name__}
                    ))
                    continue
                
                # Check if key is permissible
                if permissible_keys and key not in permissible_keys:
                    suggestions = self._find_similar_keys(key, permissible_keys)
                    suggestion_msg = f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
                    result.add_error(ValidationError(
                        f'points.{key}', 
                        f'Unknown point key "{key}"{suggestion_msg}',
                        context={'key': key, 'suggestions': suggestions}
                    ))
                    continue
                
                # Validate series
                if not isinstance(series, list):
                    result.add_error(ValidationError(
                        f'points.{key}', 
                        f'Point series for "{key}" must be a list',
                        context={'key': key, 'series_type': type(series).__name__}
                    ))
                    continue
                
                if len(series) == 0:
                    result.add_error(ValidationError(
                        f'points.{key}', 
                        f'Point series for "{key}" cannot be empty',
                        context={'key': key}
                    ))
                    continue
                
                # Validate each point in the series
                times = []
                for i, point in enumerate(series):
                    if not isinstance(point, (list, tuple)) or len(point) != 2:
                        result.add_error(ValidationError(
                            f'points.{key}[{i}]', 
                            f'Point {i} in series "{key}" must be a list/tuple of 2 numbers',
                            context={'key': key, 'index': i, 'point': point}
                        ))
                        continue
                    
                    try:
                        time_val = float(point[0])
                        value_val = float(point[1])
                        times.append(time_val)
                        
                        # Validate value constraints
                        if value_val < 0 and self._is_negative_invalid(key):
                            result.add_error(ValidationError(
                                f'points.{key}[{i}]', 
                                f'Value at point {i} in series "{key}" cannot be negative',
                                context={'key': key, 'index': i, 'value': value_val}
                            ))
                        
                    except (ValueError, TypeError):
                        result.add_error(ValidationError(
                            f'points.{key}[{i}]', 
                            f'Point {i} in series "{key}" must contain valid numbers',
                            context={'key': key, 'index': i, 'point': point}
                        ))
                
                # Check for time ordering
                if len(times) > 1:
                    sorted_times = sorted(times)
                    if times != sorted_times:
                        result.add_error(ValidationError(
                            f'points.{key}', 
                            f'Point series "{key}" must be sorted by time',
                            context={'key': key, 'times': times}
                        ))
            
        except Exception as e:
            result.add_error(ValidationError(
                'points', 
                f'Unexpected error validating points: {e}',
                context={'exception': str(e)}
            ))
        
        return result
    
    def validate_primary_map(self, primary_map: Dict, available_sectors: Optional[Set[str]] = None, 
                           available_products: Optional[Set[str]] = None) -> ValidationResult:
        """Validate primary map overrides.
        
        Args:
            primary_map: Primary map dictionary to validate
            available_sectors: Set of available sectors
            available_products: Set of available products
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult()
        
        try:
            if not isinstance(primary_map, dict):
                result.add_error(ValidationError(
                    'primary_map', 
                    'Primary map must be a dictionary',
                    context={'type': type(primary_map).__name__}
                ))
                return result
            
            for sector, entries in primary_map.items():
                # Validate sector
                if not isinstance(sector, str):
                    result.add_error(ValidationError(
                        f'primary_map.{sector}', 
                        'Sector must be a string',
                        context={'sector': sector, 'sector_type': type(sector).__name__}
                    ))
                    continue
                
                if available_sectors and sector not in available_sectors:
                    suggestions = self._find_similar_keys(sector, available_sectors)
                    suggestion_msg = f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
                    result.add_error(ValidationError(
                        f'primary_map.{sector}', 
                        f'Unknown sector "{sector}"{suggestion_msg}',
                        context={'sector': sector, 'suggestions': suggestions}
                    ))
                    continue
                
                # Validate entries
                if not isinstance(entries, list):
                    result.add_error(ValidationError(
                        f'primary_map.{sector}', 
                        f'Entries for sector "{sector}" must be a list',
                        context={'sector': sector, 'entries_type': type(entries).__name__}
                    ))
                    continue
                
                for i, entry in enumerate(entries):
                    if not isinstance(entry, dict):
                        result.add_error(ValidationError(
                            f'primary_map.{sector}[{i}]', 
                            f'Entry {i} for sector "{sector}" must be a dictionary',
                            context={'sector': sector, 'index': i, 'entry': entry}
                        ))
                        continue
                    
                    # Validate product
                    product = entry.get('product')
                    if not isinstance(product, str):
                        result.add_error(ValidationError(
                            f'primary_map.{sector}[{i}].product', 
                            f'Product in entry {i} for sector "{sector}" must be a string',
                            context={'sector': sector, 'index': i, 'product': product}
                        ))
                    elif available_products and product not in available_products:
                        suggestions = self._find_similar_keys(product, available_products)
                        suggestion_msg = f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
                        result.add_error(ValidationError(
                            f'primary_map.{sector}[{i}].product', 
                            f'Unknown product "{product}" in entry {i} for sector "{sector}"{suggestion_msg}',
                            context={'sector': sector, 'index': i, 'product': product, 'suggestions': suggestions}
                        ))
                    
                    # Validate start_year
                    start_year = entry.get('start_year')
                    try:
                        start_year_val = float(start_year)
                        if start_year_val < 0:
                            result.add_error(ValidationError(
                                f'primary_map.{sector}[{i}].start_year', 
                                f'Start year in entry {i} for sector "{sector}" cannot be negative',
                                context={'sector': sector, 'index': i, 'start_year': start_year_val}
                            ))
                    except (ValueError, TypeError):
                        result.add_error(ValidationError(
                            f'primary_map.{sector}[{i}].start_year', 
                            f'Start year in entry {i} for sector "{sector}" must be a valid number',
                            context={'sector': sector, 'index': i, 'start_year': start_year}
                        ))
            
        except Exception as e:
            result.add_error(ValidationError(
                'primary_map', 
                f'Unexpected error validating primary map: {e}',
                context={'exception': str(e)}
            ))
        
        return result
    
    def validate_seeds(self, seeds: Dict, available_sectors: Optional[Set[str]] = None,
                      available_products: Optional[Set[str]] = None) -> ValidationResult:
        """Validate seeds configuration.
        
        Args:
            seeds: Seeds dictionary to validate
            available_sectors: Set of available sectors
            available_products: Set of available products
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult()
        
        try:
            if not isinstance(seeds, dict):
                result.add_error(ValidationError(
                    'seeds', 
                    'Seeds must be a dictionary',
                    context={'type': type(seeds).__name__}
                ))
                return result
            
            # Validate simple seed types
            for seed_type in ['active_anchor_clients', 'elapsed_quarters', 'direct_clients', 'completed_projects']:
                if seed_type in seeds:
                    seed_data = seeds[seed_type]
                    if not isinstance(seed_data, dict):
                        result.add_error(ValidationError(
                            f'seeds.{seed_type}', 
                            f'Seed field "{seed_type}" must be a dictionary',
                            context={'seed_type': seed_type, 'type': type(seed_data).__name__}
                        ))
                        continue
                    
                    for key, value in seed_data.items():
                        if not isinstance(key, str):
                            result.add_error(ValidationError(
                                f'seeds.{seed_type}.{key}', 
                                f'Seed key in "{seed_type}" must be a string',
                                context={'seed_type': seed_type, 'key': key, 'key_type': type(key).__name__}
                            ))
                            continue
                        
                        # Validate sector/product existence
                        if seed_type in ['active_anchor_clients', 'elapsed_quarters', 'completed_projects']:
                            if available_sectors and key not in available_sectors:
                                suggestions = self._find_similar_keys(key, available_sectors)
                                suggestion_msg = f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
                                result.add_error(ValidationError(
                                    f'seeds.{seed_type}.{key}', 
                                    f'Unknown sector "{key}" in "{seed_type}"{suggestion_msg}',
                                    context={'seed_type': seed_type, 'key': key, 'suggestions': suggestions}
                                ))
                        
                        elif seed_type == 'direct_clients':
                            if available_products and key not in available_products:
                                suggestions = self._find_similar_keys(key, available_products)
                                suggestion_msg = f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
                                result.add_error(ValidationError(
                                    f'seeds.{seed_type}.{key}', 
                                    f'Unknown product "{key}" in "{seed_type}"{suggestion_msg}',
                                    context={'seed_type': seed_type, 'key': key, 'suggestions': suggestions}
                                ))
                        
                        # Validate value
                        try:
                            int_val = int(value)
                            if int_val < 0:
                                result.add_error(ValidationError(
                                    f'seeds.{seed_type}.{key}', 
                                    f'Seed value for "{key}" in "{seed_type}" cannot be negative',
                                    context={'seed_type': seed_type, 'key': key, 'value': int_val}
                                ))
                        except (ValueError, TypeError):
                            result.add_error(ValidationError(
                                f'seeds.{seed_type}.{key}', 
                                f'Seed value for "{key}" in "{seed_type}" must be a valid integer',
                                context={'seed_type': seed_type, 'key': key, 'value': value}
                            ))
            
            # Validate SM-mode seeds
            for seed_type in ['active_anchor_clients_sm', 'completed_projects_sm']:
                if seed_type in seeds:
                    seed_data = seeds[seed_type]
                    if not isinstance(seed_data, dict):
                        result.add_error(ValidationError(
                            f'seeds.{seed_type}', 
                            f'Seed field "{seed_type}" must be a dictionary',
                            context={'seed_type': seed_type, 'type': type(seed_data).__name__}
                        ))
                        continue
                    
                    for sector, products in seed_data.items():
                        if not isinstance(sector, str):
                            result.add_error(ValidationError(
                                f'seeds.{seed_type}.{sector}', 
                                f'Sector key in "{seed_type}" must be a string',
                                context={'seed_type': seed_type, 'sector': sector, 'sector_type': type(sector).__name__}
                            ))
                            continue
                        
                        if available_sectors and sector not in available_sectors:
                            suggestions = self._find_similar_keys(sector, available_sectors)
                            suggestion_msg = f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
                            result.add_error(ValidationError(
                                f'seeds.{seed_type}.{sector}', 
                                f'Unknown sector "{sector}" in "{seed_type}"{suggestion_msg}',
                                context={'seed_type': seed_type, 'sector': sector, 'suggestions': suggestions}
                            ))
                            continue
                        
                        if not isinstance(products, dict):
                            result.add_error(ValidationError(
                                f'seeds.{seed_type}.{sector}', 
                                f'Products for sector "{sector}" in "{seed_type}" must be a dictionary',
                                context={'seed_type': seed_type, 'sector': sector, 'products_type': type(products).__name__}
                            ))
                            continue
                        
                        for product, value in products.items():
                            if not isinstance(product, str):
                                result.add_error(ValidationError(
                                    f'seeds.{seed_type}.{sector}.{product}', 
                                    f'Product key for sector "{sector}" in "{seed_type}" must be a string',
                                    context={'seed_type': seed_type, 'sector': sector, 'product': product, 'product_type': type(product).__name__}
                                ))
                                continue
                            
                            if available_products and product not in available_products:
                                suggestions = self._find_similar_keys(product, available_products)
                                suggestion_msg = f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
                                result.add_error(ValidationError(
                                    f'seeds.{seed_type}.{sector}.{product}', 
                                    f'Unknown product "{product}" for sector "{sector}" in "{seed_type}"{suggestion_msg}',
                                    context={'seed_type': seed_type, 'sector': sector, 'product': product, 'suggestions': suggestions}
                                ))
                                continue
                            
                            try:
                                int_val = int(value)
                                if int_val < 0:
                                    result.add_error(ValidationError(
                                        f'seeds.{seed_type}.{sector}.{product}', 
                                        f'Seed value for product "{product}" in sector "{sector}" in "{seed_type}" cannot be negative',
                                        context={'seed_type': seed_type, 'sector': sector, 'product': product, 'value': int_val}
                                    ))
                            except (ValueError, TypeError):
                                result.add_error(ValidationError(
                                    f'seeds.{seed_type}.{sector}.{product}', 
                                    f'Seed value for product "{product}" in sector "{sector}" in "{seed_type}" must be a valid integer',
                                    context={'seed_type': seed_type, 'sector': sector, 'product': product, 'value': value}
                                ))
            
        except Exception as e:
            result.add_error(ValidationError(
                'seeds', 
                f'Unexpected error validating seeds: {e}',
                context={'exception': str(e)}
            ))
        
        return result
    
    def validate_scenario(self, scenario_data: Dict, permissible_keys: Optional[Dict] = None) -> ValidationResult:
        """Validate a complete scenario.
        
        Args:
            scenario_data: Complete scenario data to validate
            permissible_keys: Dictionary of permissible keys for different sections
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult()
        
        try:
            # Validate basic structure
            if not isinstance(scenario_data, dict):
                result.add_error(ValidationError(
                    'scenario', 
                    'Scenario data must be a dictionary',
                    context={'type': type(scenario_data).__name__}
                ))
                return result
            
            # Validate name
            if 'name' not in scenario_data:
                result.add_error(ValidationError(
                    'name', 
                    'Scenario must have a name'
                ))
            elif not isinstance(scenario_data['name'], str):
                result.add_error(ValidationError(
                    'name', 
                    'Scenario name must be a string',
                    context={'name': scenario_data['name']}
                ))
            
            # Validate runspecs
            if 'runspecs' in scenario_data:
                runspecs_result = self.validate_runspecs(scenario_data['runspecs'])
                result.add_errors(runspecs_result.errors)
            
            # Validate overrides
            if 'overrides' in scenario_data:
                overrides = scenario_data['overrides']
                if not isinstance(overrides, dict):
                    result.add_error(ValidationError(
                        'overrides', 
                        'Overrides must be a dictionary',
                        context={'type': type(overrides).__name__}
                    ))
                else:
                    # Validate constants
                    if 'constants' in overrides:
                        const_keys = permissible_keys.get('constants') if permissible_keys else None
                        constants_result = self.validate_constants(overrides['constants'], const_keys)
                        result.add_errors(constants_result.errors)
                    
                    # Validate points
                    if 'points' in overrides:
                        point_keys = permissible_keys.get('points') if permissible_keys else None
                        points_result = self.validate_points(overrides['points'], point_keys)
                        result.add_errors(points_result.errors)
                    
                    # Validate primary_map
                    if 'primary_map' in overrides:
                        sectors = permissible_keys.get('sectors') if permissible_keys else None
                        products = permissible_keys.get('products') if permissible_keys else None
                        primary_map_result = self.validate_primary_map(overrides['primary_map'], sectors, products)
                        result.add_errors(primary_map_result.errors)
            
            # Validate seeds
            if 'seeds' in scenario_data:
                sectors = permissible_keys.get('sectors') if permissible_keys else None
                products = permissible_keys.get('products') if permissible_keys else None
                seeds_result = self.validate_seeds(scenario_data['seeds'], sectors, products)
                result.add_errors(seeds_result.errors)
            
        except Exception as e:
            result.add_error(ValidationError(
                'scenario', 
                f'Unexpected error validating scenario: {e}',
                context={'exception': str(e)}
            ))
        
        return result
    
    def validate_current_state(self, permissible_keys: Optional[Dict] = None) -> ValidationResult:
        """Validate the current application state.
        
        Args:
            permissible_keys: Dictionary of permissible keys for different sections
            
        Returns:
            ValidationResult with validation status and errors
        """
        try:
            # Convert current state to scenario data
            scenario_data = self.state_manager.to_scenario_dict_normalized()
            
            # Validate the scenario
            return self.validate_scenario(scenario_data, permissible_keys)
            
        except Exception as e:
            result = ValidationResult()
            result.add_error(ValidationError(
                'state', 
                f'Error validating current state: {e}',
                context={'exception': str(e)}
            ))
            return result
    
    def _find_similar_keys(self, target: str, available_keys: Set[str], max_distance: int = 3) -> List[str]:
        """Find similar keys using Levenshtein distance.
        
        Args:
            target: Target key to find similar keys for
            available_keys: Set of available keys
            max_distance: Maximum Levenshtein distance for similarity
            
        Returns:
            List of similar keys sorted by similarity
        """
        try:
            from difflib import SequenceMatcher
            
            similar_keys = []
            for key in available_keys:
                similarity = SequenceMatcher(None, target.lower(), key.lower()).ratio()
                if similarity > 0.6:  # 60% similarity threshold
                    similar_keys.append((key, similarity))
            
            # Sort by similarity (highest first)
            similar_keys.sort(key=lambda x: x[1], reverse=True)
            return [key for key, _ in similar_keys[:5]]  # Return top 5 matches
            
        except ImportError:
            # Fallback to simple string matching if difflib is not available
            target_lower = target.lower()
            similar_keys = []
            for key in available_keys:
                if target_lower in key.lower() or key.lower() in target_lower:
                    similar_keys.append(key)
            return similar_keys[:5]
    
    def _is_negative_invalid(self, key: str) -> bool:
        """Check if a key cannot have negative values.
        
        Args:
            key: The key to check
            
        Returns:
            True if negative values are invalid for this key
        """
        # Keys that cannot be negative
        non_negative_keys = {
            'anchor_lead_generation_rate', 'lead_to_pc_conversion_rate', 'project_generation_rate',
            'max_projects_per_pc', 'project_duration', 'projects_to_client_conversion',
            'initial_phase_duration', 'ramp_phase_duration', 'initial_requirement_rate',
            'ramp_requirement_rate', 'steady_requirement_rate', 'requirement_to_order_lag',
            'ATAM', 'inbound_lead_generation_rate', 'outbound_lead_generation_rate',
            'lead_to_c_conversion_rate', 'lead_to_requirement_delay', 'requirement_to_fulfilment_delay',
            'avg_order_quantity_initial', 'client_requirement_growth', 'TAM'
        }
        
        return key in non_negative_keys
