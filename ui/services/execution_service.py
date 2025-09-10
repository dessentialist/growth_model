from __future__ import annotations

"""Execution service: run simulations and query status (Phase 4).

This service launches the repository's stepwise runner `simulate_growth.py`
as a subprocess, persists minimal metadata to `logs/` so Streamlit reruns
can detect running state, and provides simple log tailing helpers.

Design goals:
- Avoid extra dependencies (no psutil); use POSIX pid checks on macOS.
- Persist PID and run metadata to JSON under `logs/` for durability.
- Keep the API narrow and UI-friendly.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import os
import signal
import subprocess
import sys
import time

from src.io_paths import LOGS_DIR, SCENARIOS_DIR, OUTPUT_DIR


_PID_FILE = LOGS_DIR / "ui_runner_pid.json"
_HISTORY_FILE = LOGS_DIR / "ui_execution_history.json"
_RUN_LOG_FILE = LOGS_DIR / "run.log"


@dataclass
class RunMeta:
    """Metadata persisted for a single run."""

    pid: int
    scenario_name: str
    scenario_path: str
    args: List[str]
    started_at_epoch: float


class ExecutionService:
    """Run `simulate_growth.py` and inspect status/history.

    The UI should save and validate a scenario file first, then pass the
    absolute path here along with desired flags.
    """

    def __init__(self) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Run control ---
    def run_simulation(
        self,
        *,
        scenario_path: Path,
        output_name: str | None = None,
        debug: bool = False,
        visualize: bool = False,
        kpi_sm_revenue_rows: bool = False,
        kpi_sm_client_rows: bool = False,
    ) -> Tuple[bool, str]:
        """Start the simulation as a background subprocess.

        Args:
            scenario_path: Absolute path to a saved scenario YAML/JSON.
            debug: Enable runner debug logging.
            visualize: Generate plots after run.
            kpi_sm_revenue_rows: Include per-(sector, product) revenue rows.
            kpi_sm_client_rows: Include per-(sector, product) client rows.

        Returns:
            (ok, message) indicating whether the process was started.
        """
        try:
            scenario_path = Path(scenario_path).resolve()
        except Exception:
            return False, "Invalid scenario path"

        if not scenario_path.exists():
            return False, f"Scenario file not found: {scenario_path}"

        # If a run is already active, refuse to start a new one
        status = self.get_execution_status()
        if status.get("running"):
            return False, "A simulation is already running"

        # Build command: use current Python interpreter to run simulate_growth.py
        repo_root = Path(__file__).resolve().parents[2]
        runner_script = repo_root / "simulate_growth.py"
        if not runner_script.exists():
            return False, f"Runner script not found: {runner_script}"

        cmd: List[str] = [
            sys.executable,
            str(runner_script),
            "--scenario",
            str(scenario_path),
        ]
        if debug:
            cmd.append("--debug")
        if visualize:
            cmd.append("--visualize")
        if kpi_sm_revenue_rows:
            cmd.append("--kpi-sm-revenue-rows")
        if kpi_sm_client_rows:
            cmd.append("--kpi-sm-client-rows")
        if isinstance(output_name, str) and output_name.strip():
            cmd.extend(["--output-name", output_name.strip()])

        # Ensure log file exists to be tailed immediately
        try:
            _RUN_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            if not _RUN_LOG_FILE.exists():
                _RUN_LOG_FILE.touch()
        except Exception:
            # Non-fatal; the runner will create it on first log write
            pass

        # Write a breadcrumb line with the exact command
        try:
            _RUN_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with _RUN_LOG_FILE.open("a", encoding="utf-8") as lf:
                lf.write(f"UI: starting: {' '.join(cmd)}\n")
        except Exception:
            pass

        # Launch subprocess; inherit environment, set cwd to repo root so relative paths work
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(repo_root),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                close_fds=True,
            )
        except Exception as exc:
            return False, f"Failed to start runner: {exc}"

        # Persist PID metadata
        meta = RunMeta(
            pid=int(proc.pid),
            scenario_name=Path(scenario_path).stem,
            scenario_path=str(scenario_path),
            args=cmd[1:],  # omit interpreter for readability
            started_at_epoch=time.time(),
        )
        self._write_pid_file(meta)
        self._append_history(meta)
        return True, f"Started PID {proc.pid}"

    def stop_simulation(self) -> Tuple[bool, str]:
        """Attempt to stop a running simulation.

        Sends SIGTERM; if the process persists briefly, reports that it may still
        be terminating. Caller can poll `get_execution_status`.
        """
        meta = self._read_pid_file()
        if meta is None:
            return False, "No active run"
        pid = int(meta.get("pid", 0))
        if pid <= 0:
            return False, "Invalid PID in metadata"
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            # Already gone; clean up pid file
            self._remove_pid_file()
            return True, "Process already exited"
        except Exception as exc:
            return False, f"Failed to terminate process: {exc}"
        # Give a brief moment before claiming success
        time.sleep(0.2)
        return True, "Terminate signal sent"

    # --- Status & history ---
    def get_execution_status(self) -> Dict[str, Any]:
        """Return a lightweight status snapshot for the current run if any.

        Fields:
            running: bool
            pid: int | None
            scenario_name: str | ""
            started_at_epoch: float | 0.0
            last_log_lines: list[str] (up to 40 lines)
        """
        meta = self._read_pid_file()
        status: Dict[str, Any] = {
            "running": False,
            "pid": None,
            "scenario_name": "",
            "started_at_epoch": 0.0,
            "last_log_lines": [],
        }
        if not meta:
            status["last_log_lines"] = self.tail_log(max_lines=40)
            return status
        pid = int(meta.get("pid", 0))
        status.update({
            "pid": pid or None,
            "scenario_name": str(meta.get("scenario_name", "")),
            "started_at_epoch": float(meta.get("started_at_epoch", 0.0)),
        })
        if pid > 0 and self._pid_is_runner(pid):
            status["running"] = True
        else:
            # Clear stale pid file
            self._remove_pid_file()
        # Read log tail and detect completion patterns
        tail = self.tail_log(max_lines=80)
        status["last_log_lines"] = tail
        if status["running"]:
            try:
                joined = "\n".join(tail)
                if ("Wrote KPI CSV" in joined) or ("OK: Phase" in joined) or ("OK:" in joined):
                    # Consider the run complete even if PID still appears; clear pid file
                    self._remove_pid_file()
                    status["running"] = False
            except Exception:
                pass

        return status

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Return prior run metadata entries (most recent first)."""
        try:
            if _HISTORY_FILE.exists():
                data = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return list(reversed(data))
        except Exception:
            pass
        return []

    # --- Logs ---
    def tail_log(self, *, max_lines: int = 200, level: str | None = None, contains: str | None = None) -> List[str]:
        """Return up to the last `max_lines` from logs/run.log with optional filtering.

        Args:
            max_lines: Maximum number of lines to return from the end of the file.
            level: Optional minimum level filter (DEBUG, INFO, WARNING, ERROR).
            contains: Optional substring filter applied after level filtering.
        """
        try:
            if not _RUN_LOG_FILE.exists():
                return []
            # Efficient tail: read all and slice (log size is moderate). For very large
            # files, a streaming tail could be added later.
            lines = _RUN_LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return []
        # Level filter: keep lines that contain the level token
        if isinstance(level, str) and level:
            token = level.upper()
            lines = [ln for ln in lines if token in ln]
        # Contains filter
        if isinstance(contains, str) and contains:
            lines = [ln for ln in lines if contains in ln]
        # Return the tail
        if max_lines > 0 and len(lines) > max_lines:
            return lines[-max_lines:]
        return lines

    def read_log_full(self, *, level: str | None = None, contains: str | None = None) -> List[str]:
        """Return the entire log file with optional filtering.

        Args:
            level: Optional minimum level token to include (e.g., INFO, DEBUG).
            contains: Optional substring filter applied after level filtering.
        """
        try:
            if not _RUN_LOG_FILE.exists():
                return []
            lines = _RUN_LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return []
        if isinstance(level, str) and level:
            token = level.upper()
            lines = [ln for ln in lines if token in ln]
        if isinstance(contains, str) and contains:
            lines = [ln for ln in lines if contains in ln]
        return lines

    def read_log_from_last_session(self, *, level: str | None = None, contains: str | None = None) -> List[str]:
        """Return log lines starting from the last UI session start marker.

        We write a breadcrumb line before launching the runner: "UI: starting: ...".
        This method finds the last such marker and returns lines from there.
        If the marker is not found, returns the full file (filtered).
        """
        try:
            if not _RUN_LOG_FILE.exists():
                return []
            lines = _RUN_LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return []
        # Find last marker index
        start_idx = -1
        marker = "UI: starting: "
        for idx in range(len(lines) - 1, -1, -1):
            if marker in lines[idx]:
                start_idx = idx
                break
        if start_idx >= 0:
            sub = lines[start_idx:]
        else:
            sub = lines
        if isinstance(level, str) and level:
            token = level.upper()
            sub = [ln for ln in sub if token in ln]
        if isinstance(contains, str) and contains:
            sub = [ln for ln in sub if contains in ln]
        return sub

    def log_stats(self) -> Dict[str, Any]:
        """Return basic statistics about the log file for UI display."""
        try:
            if not _RUN_LOG_FILE.exists():
                return {"exists": False}
            st = _RUN_LOG_FILE.stat()
            return {
                "exists": True,
                "size_bytes": int(st.st_size),
                "modified_epoch": float(st.st_mtime),
                "path": str(_RUN_LOG_FILE),
            }
        except Exception:
            return {"exists": False}

    # --- Internals ---
    def _pid_is_runner(self, pid: int) -> bool:
        """Check whether PID exists and corresponds to our runner (simulate_growth.py)."""
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            # May exist; continue to ps check
            pass
        except Exception:
            return False
        try:
            out = subprocess.check_output(["ps", "-o", "command=", "-p", str(pid)], stderr=subprocess.DEVNULL)
            cmd = out.decode("utf-8", errors="ignore").strip()
            return "simulate_growth.py" in cmd
        except Exception:
            # Fallback to existence only
            return True

    def _write_pid_file(self, meta: RunMeta) -> None:
        try:
            payload = asdict(meta)
            with _PID_FILE.open("w", encoding="utf-8") as f:
                json.dump(payload, f)
        except Exception:
            # Non-fatal
            pass

    def _read_pid_file(self) -> Dict[str, Any] | None:
        try:
            if not _PID_FILE.exists():
                return None
            with _PID_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            return None
        return None

    def _remove_pid_file(self) -> None:
        try:
            if _PID_FILE.exists():
                _PID_FILE.unlink()
        except Exception:
            pass

    def _append_history(self, meta: RunMeta) -> None:
        try:
            existing: List[Dict[str, Any]] = []
            if _HISTORY_FILE.exists():
                existing = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = []
            existing.append(asdict(meta))
            _HISTORY_FILE.write_text(json.dumps(existing), encoding="utf-8")
        except Exception:
            # Non-fatal
            pass

    # --- Maintenance ---
    def clear_stale_status(self) -> Tuple[bool, str]:
        """Clear pid metadata if no matching runner process is active."""
        meta = self._read_pid_file()
        if not meta:
            return True, "No active run metadata to clear"
        pid = int(meta.get("pid", 0))
        if pid <= 0 or not self._pid_is_runner(pid):
            self._remove_pid_file()
            return True, "Cleared stale run status"
        return False, f"A simulation appears to be running (PID {pid})"

    # --- Results discovery & preview helpers ---
    def get_results_csv_for_scenario(self, scenario_stem: str) -> Path | None:
        """Return most recent CSV matching a scenario stem (timestamped or suffixed)."""
        try:
            scenario_stem = str(scenario_stem).strip()
            if not scenario_stem:
                return None
            patterns = [
                f"Product_Growth_System_Complete_Results_{scenario_stem}.csv",
                f"Growth_System_Complete_Results_{scenario_stem}.csv",
                f"*{scenario_stem}_????????????.csv",
                f"*{scenario_stem}*.csv",
            ]
            candidates: list[Path] = []
            for pattern in patterns:
                candidates.extend(OUTPUT_DIR.glob(pattern))
            uniq = sorted({p.resolve() for p in candidates if p.is_file()}, key=lambda p: p.stat().st_mtime, reverse=True)
            if uniq:
                return uniq[0]
            return self.get_latest_results_csv()
        except Exception:
            return None

    def get_latest_results_csv(self) -> Path | None:
        """Return the most recent CSV in output/ regardless of scenario."""
        try:
            patterns = [
                "Product_Growth_System_Complete_Results*.csv",
                "Growth_System_Complete_Results*.csv",
                "*Complete_Results*.csv",
                "*_????????????.csv",
            ]
            candidates: list[Path] = []
            for pattern in patterns:
                candidates.extend(OUTPUT_DIR.glob(pattern))
            uniq = sorted({p.resolve() for p in candidates if p.is_file()}, key=lambda p: p.stat().st_mtime, reverse=True)
            return uniq[0] if uniq else None
        except Exception:
            return None

    def list_plot_images(self) -> list[Path]:
        """List recent PNG plots under output/plots sorted by mtime desc."""
        try:
            plots_dir = OUTPUT_DIR / "plots"
            if not plots_dir.exists():
                return []
            images = [p.resolve() for p in plots_dir.glob("*.png") if p.is_file()]
            images.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return images
        except Exception:
            return []

    def read_csv_head(self, path: Path, *, max_rows: int = 30) -> dict | None:
        """Return small CSV preview as {columns: [...], rows: [[...]]}."""
        try:
            import pandas as pd  # local import

            df = pd.read_csv(path)
            if max_rows > 0:
                df = df.head(max_rows)
            return {"columns": list(df.columns.astype(str)), "rows": df.astype(object).values.tolist()}
        except Exception:
            return None


