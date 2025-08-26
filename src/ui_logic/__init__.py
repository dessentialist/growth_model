"""
Framework-agnostic business logic for the Growth Model UI.

This module contains all business logic that was previously embedded in UI components.
The logic is designed to be completely independent of any UI framework (Streamlit, Svelte, etc.)
and can be used by any frontend implementation.

Core principles:
- No UI framework imports or dependencies
- Pure business logic with clear interfaces
- Comprehensive validation and error handling
- Reactive state management patterns
- Centralized configuration management
"""

from .state_manager import StateManager
from .scenario_manager import ScenarioManager
from .validation_manager import ValidationManager
from .runner_manager import RunnerManager
from .data_manager import DataManager

__all__ = [
    "StateManager",
    "ScenarioManager", 
    "ValidationManager",
    "RunnerManager",
    "DataManager",
]
