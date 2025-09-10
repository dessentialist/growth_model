from __future__ import annotations

"""Validation helpers for UI input fields and scenarios.

Keeps simple input checks local to the UI while delegating full scenario
validation to the backend via ScenarioService when needed.
"""

from typing import Dict, List, Tuple, Any


class ValidationService:
    """Lightweight validators for common UI inputs."""

    def validate_positive_number(self, name: str, value: Any) -> Tuple[bool, str]:
        try:
            numeric = float(value)
            if numeric < 0:
                return False, f"{name} must be non-negative"
            return True, ""
        except Exception:
            return False, f"{name} must be a number"

    def validate_runtime(self, start: Any, stop: Any, dt: Any) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        try:
            start_f = float(start)
            stop_f = float(stop)
            dt_f = float(dt)
            if stop_f <= start_f:
                errors.append("stoptime must be greater than starttime")
            if dt_f <= 0:
                errors.append("dt must be > 0")
        except Exception:
            errors.append("starttime, stoptime, and dt must be numbers")
        return len(errors) == 0, errors


