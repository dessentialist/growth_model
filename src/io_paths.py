from __future__ import annotations

"""Centralized path utilities for the project.

These provide absolute `Path` objects to key directories, avoiding
hard-coded relative paths throughout the codebase and improving
portability across environments.
"""

from pathlib import Path


# The `src` directory is one level below the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Canonical directories used throughout the project
INPUTS_DIR = PROJECT_ROOT / "Inputs"
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
