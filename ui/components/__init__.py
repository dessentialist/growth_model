"""UI components package for the rebuilt Streamlit application.

This package contains base component classes and tab implementations.
Each tab should define a class inheriting from `BaseComponent` with a
`render()` method that draws the UI for that tab and optionally a
`save_changes()` method to persist edits via services.
"""

from .base_component import BaseComponent  # re-export for convenience

__all__ = [
    "BaseComponent",
]


