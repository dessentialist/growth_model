from __future__ import annotations

"""
Thin client helpers for validating UI-built scenarios against backend rules.

This module intentionally avoids Streamlit imports and only orchestrates calls
to `src.phase1_data` and `src.scenario_loader` so the UI can request:
 - Phase1 bundle loading and caching (done by the caller/UI)
 - Listing permissible override keys for the current mode
 - Validating a scenario dict and returning a rich error message
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.phase1_data import load_phase1_inputs, Phase1Bundle
from src.scenario_loader import (
    list_permissible_override_keys,
    validate_scenario_dict,
)


@dataclass(frozen=True)
class PermissibleKeys:
    constants: List[str]
    points: List[str]


def get_bundle() -> Phase1Bundle:
    """Load and return the Phase1 bundle.

    Callers should cache this value at the UI layer to avoid reloading on every
    interaction. We keep this function simple and without caching here to avoid
    global state in a non-UI module.
    """
    return load_phase1_inputs()


def get_permissible_keys(bundle: Phase1Bundle, *, anchor_mode: str = "sector",
                         extra_sm_pairs: Optional[List[Tuple[str, str]]] = None) -> PermissibleKeys:
    """Return sorted lists of permissible constant and points keys."""
    data = list_permissible_override_keys(bundle, anchor_mode=anchor_mode, extra_sm_pairs=extra_sm_pairs)
    return PermissibleKeys(constants=sorted(data["constants"]), points=sorted(data["points"]))


def try_validate_scenario_dict(bundle: Phase1Bundle, scenario_dict: dict) -> tuple[bool, Optional[str]]:
    """Validate a scenario dict. Returns (ok, error_message_or_None).

    We keep the error surface concise and helpful for the UI, converting Python
    exceptions into user-friendly strings without losing key context.
    """
    try:
        _ = validate_scenario_dict(bundle, scenario_dict)
        return True, None
    except Exception as e:
        return False, str(e)


__all__ = [
    "PermissibleKeys",
    "get_bundle",
    "get_permissible_keys",
    "try_validate_scenario_dict",
]


