from __future__ import annotations

"""
Runner integration helpers for the Streamlit UI layer.

This module contains only the functions required to execute the
`simulate_fff_growth.py` runner and to surface logs/results back to the UI.

Design goals:
- Keep responsibilities focused on process execution and artifact discovery
- Avoid any Streamlit imports or UI-specific state
- Provide small, composable functions that are easy to test

Functions provided:
- build_runner_command: construct CLI args for the runner
- run_simulation: blocking execution with exit code
- start_simulation_process: non-blocking execution returning a Popen
- terminate_process: best-effort termination of a running process
- read_log_tail: efficient tail of the latest lines in logs/run.log
- find_latest_results_csv: discover newest KPI CSV under output/
- generate_plots_from_csv: optional Phase 12 visualization
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.io_paths import LOGS_DIR, OUTPUT_DIR, PROJECT_ROOT


@dataclass(frozen=True)
class RunnerCommand:
    """Simple container for the runner command and working directory.

    Attributes
    - cmd: list of command tokens to execute via subprocess
    - cwd: working directory (project root)
    """

    cmd: list[str]
    cwd: Path


def build_runner_command(
    scenario_path: Optional[Path] = None,
    preset: Optional[str] = None,
    debug: bool = False,
    visualize: bool = False,
    kpi_sm_revenue_rows: bool = False,
    kpi_sm_client_rows: bool = False,
    python_executable: str = "python",
) -> RunnerCommand:
    """Construct the non-interactive CLI command for the runner.

    Exactly one of `scenario_path` or `preset` may be provided. If neither is
    provided, default to the baseline preset via `--preset baseline`.
    """
    args: list[str] = [python_executable, str(PROJECT_ROOT / "simulate_fff_growth.py")]
    if scenario_path is not None and preset is not None:
        raise ValueError("Provide only one of scenario_path or preset")
    if scenario_path is not None:
        args += ["--scenario", str(scenario_path)]
    elif preset is not None:
        args += ["--preset", str(preset)]
    else:
        args += ["--preset", "baseline"]
    if debug:
        args.append("--debug")
    if visualize:
        args.append("--visualize")
    if kpi_sm_revenue_rows:
        args.append("--kpi-sm-revenue-rows")
    if kpi_sm_client_rows:
        args.append("--kpi-sm-client-rows")
    return RunnerCommand(cmd=args, cwd=PROJECT_ROOT)


def run_simulation(rc: RunnerCommand, env: Optional[dict] = None) -> int:
    """Run the simulation once and return the exit code.

    - Uses the project root as the working directory
    - Inherit environment with optional overrides
    - Non-interactive; blocks until the process exits
    """
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(rc.cmd, cwd=str(rc.cwd), env=merged_env, check=False)
    return int(proc.returncode)


def start_simulation_process(rc: RunnerCommand, env: Optional[dict] = None) -> subprocess.Popen:
    """Start the simulation as a subprocess and return the Popen handle.

    This enables basic log polling during execution from the UI layer.
    """
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.Popen(rc.cmd, cwd=str(rc.cwd), env=merged_env)


def terminate_process(proc: subprocess.Popen) -> None:
    """Terminate a running process if still alive (best-effort)."""
    if proc.poll() is None:
        try:
            proc.terminate()
        except Exception:
            pass


def read_log_tail(max_lines: int = 500) -> list[str]:
    """Return the last `max_lines` from logs/run.log efficiently.

    Implementation notes:
    - Avoid reading the entire file every time; seek near the end and split
    - For very small files, this behaves like a full read
    - We limit the window to ~128 KiB which comfortably covers hundreds of lines
    """
    log_path = LOGS_DIR / "run.log"
    if not log_path.exists():
        return []

    try:
        window_bytes = 128 * 1024  # 128 KiB window near EOF
        size = log_path.stat().st_size
        start = max(0, size - window_bytes)
        with open(log_path, "rb") as fh:
            fh.seek(start)
            data = fh.read()
        # Decode with fallback and split lines
        text = data.decode("utf-8", errors="ignore")
        lines = text.splitlines()
        return lines[-max_lines:] if len(lines) > max_lines else lines
    except Exception:
        # Fallback to the simple but less efficient approach on errors
        try:
            return (log_path.read_text(encoding="utf-8", errors="ignore").splitlines())[-max_lines:]
        except Exception:
            return []


def find_latest_results_csv() -> Optional[Path]:
    """Return the most recent KPI CSV path under `output/`, if any.

    Considers both the default `FFF_Growth_System_Complete_Results.csv` and
    suffixed copies `FFF_Growth_System_Complete_Results_<scenario>.csv`.
    """
    if not OUTPUT_DIR.exists():
        return None
    candidates: list[Path] = list(OUTPUT_DIR.glob("FFF_Growth_System_Complete_Results*.csv"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def generate_plots_from_csv(csv_path: Path) -> list[Path]:
    """Optional: Generate Phase 12 plots for a given CSV. Returns output paths."""
    from viz.plots import generate_all_plots_from_csv

    return generate_all_plots_from_csv(csv_path)


__all__ = [
    "RunnerCommand",
    "build_runner_command",
    "run_simulation",
    "start_simulation_process",
    "terminate_process",
    "read_log_tail",
    "find_latest_results_csv",
    "generate_plots_from_csv",
]
