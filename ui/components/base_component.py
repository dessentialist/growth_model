from __future__ import annotations

"""Base component class for the rebuilt Streamlit UI.

All tabs/components should inherit from `BaseComponent` and implement
the `render()` method. Components receive the central UI state and any
backend services they need through their constructor to keep them
decoupled and testable.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BaseComponent:
    """Base class for all UI components.

    Attributes:
        state: Central UI state object to read/write scenario data
    """

    state: object

    def render(self) -> None:
        """Render the component.

        Subclasses must override this method to draw Streamlit widgets
        and perform state updates via services.
        """
        raise NotImplementedError("Subclasses must implement render()")

    def save_changes(self) -> bool:
        """Persist any pending changes.

        Return True on success. Default implementation is a no-op to
        keep components lightweight when persistence isn't needed.
        """
        return True


