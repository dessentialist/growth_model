"""FFF Growth System source package.

Exports Phase 2 naming utilities for convenient imports.

Note: Phase 12 introduces a `viz` subpackage used only by the CLI runner
with the `--visualize` flag. The visualization components are imported
at runtime by `simulate_fff_growth.py` to avoid adding optional
dependencies to module import time.
"""

from .naming import *  # re-export naming helpers
from .naming import __all__ as _naming_all

# Explicitly expose the naming API when users do `from src import *`.
__all__ = list(_naming_all)

# Phase 5 ABM agents
from .abm_anchor import (  # noqa: F401
    AnchorClientAgentState,
    AnchorClientParams,
    AnchorClientAgent,
    build_anchor_agent_factory_for_sector,
    build_all_anchor_agent_factories,
)

# Extend exported API
__all__ += [
    "AnchorClientAgentState",
    "AnchorClientParams",
    "AnchorClientAgent",
    "build_anchor_agent_factory_for_sector",
    "build_all_anchor_agent_factories",
]


