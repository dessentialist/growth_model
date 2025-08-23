from __future__ import annotations

"""
Scenario assembly and YAML I/O helpers for the UI layer.

This module is intentionally focused on building and persisting scenario
structures. Runner-related helpers have been moved to `ui.services.runner` to
improve cohesion and simplify testing.
"""

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable, Optional

from src.io_paths import LOGS_DIR, OUTPUT_DIR, SCENARIOS_DIR
import yaml


def write_scenario_yaml(scenario_dict: dict, dest_path: Path) -> Path:
    """Write the given scenario dict as YAML to `dest_path` under `scenarios/`.

    - Ensures parent directory exists
    - Does not modify input dict
    - Returns the absolute path written
    """
    dest_path = Path(dest_path)
    if not dest_path.is_absolute():
        dest_path = SCENARIOS_DIR / dest_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(scenario_dict, sort_keys=False, allow_unicode=True)
    dest_path.write_text(text, encoding="utf-8")
    return dest_path


def read_scenario_yaml(path: Path) -> dict:
    """Read a YAML scenario file from disk and return as a dict."""
    path = Path(path)
    if not path.is_absolute():
        path = SCENARIOS_DIR / path
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text) or {}


def list_available_scenarios() -> list[Path]:
    """List available scenario YAML files under `scenarios/` sorted by name."""
    if not SCENARIOS_DIR.exists():
        return []
    return sorted(SCENARIOS_DIR.glob("*.y*ml"))


def read_log_tail(max_lines: int = 500) -> list[str]:
    """Backward-compatible shim for efficient tail now in `ui.services.runner`.

    Kept for import stability if any external code imports from builder.
    """
    from ui.services.runner import read_log_tail as _tail

    return _tail(max_lines)

# Backward-compatible re-exports for runner helpers previously hosted here.
# This preserves imports in older tests/modules that still reference
# `ui.services.builder` for runner operations.
from ui.services.runner import (  # noqa: E402
    RunnerCommand,
    build_runner_command,
    run_simulation,
    start_simulation_process,
    terminate_process,
    find_latest_results_csv,
    generate_plots_from_csv,
)


__all__ = [
    # Scenario I/O
    "write_scenario_yaml",
    "read_scenario_yaml",
    "list_available_scenarios",
    "read_log_tail",
    # Runner re-exports (compatibility layer)
    "RunnerCommand",
    "build_runner_command",
    "run_simulation",
    "start_simulation_process",
    "terminate_process",
    "find_latest_results_csv",
    "generate_plots_from_csv",
]