"""
Framework-agnostic runner management for the Growth Model UI.

This module handles all simulation execution and monitoring operations including:
- Building runner commands
- Starting and monitoring simulation processes
- Log streaming and monitoring
- Results processing and analysis
"""

import subprocess
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
import logging
import yaml

from .state_manager import StateManager

logger = logging.getLogger(__name__)


class RunnerCommand:
    """Represents a runner command with all its parameters."""
    
    def __init__(self, command: List[str], working_dir: Path, env: Optional[Dict[str, str]] = None):
        """Initialize a runner command.
        
        Args:
            command: List of command arguments
            working_dir: Working directory for the command
            env: Environment variables
        """
        self.command = command
        self.working_dir = working_dir
        self.env = env or {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'command': self.command,
            'working_dir': str(self.working_dir),
            'env': self.env
        }


class RunnerStatus:
    """Represents the status of a running simulation."""
    
    def __init__(self, process_id: Optional[int] = None, start_time: Optional[float] = None):
        """Initialize runner status.
        
        Args:
            process_id: Process ID of the running simulation
            start_time: Start time of the simulation
        """
        self.process_id = process_id
        self.start_time = start_time
        self.is_running = False
        self.exit_code: Optional[int] = None
        self.error_message: Optional[str] = None
        self.progress: float = 0.0
        self.current_step: Optional[str] = None
        self.log_lines: List[str] = []
        self.last_log_update: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'process_id': self.process_id,
            'start_time': self.start_time,
            'is_running': self.is_running,
            'exit_code': self.exit_code,
            'error_message': self.error_message,
            'progress': self.progress,
            'current_step': self.current_step,
            'log_lines': self.log_lines,
            'last_log_update': self.last_log_update
        }


class RunnerManager:
    """
    Framework-agnostic runner management.
    
    This class handles all simulation execution and monitoring operations including:
    - Building runner commands
    - Starting and monitoring simulation processes
    - Log streaming and monitoring
    - Results processing and analysis
    """
    
    def __init__(self, state_manager: StateManager, project_root: Path):
        """Initialize the runner manager.
        
        Args:
            state_manager: State manager instance
            project_root: Project root directory
        """
        self.state_manager = state_manager
        self.project_root = Path(project_root)
        self.current_process: Optional[subprocess.Popen] = None
        self.current_status = RunnerStatus()
        self._log_monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = False
        self._status_callbacks: List[Callable[[RunnerStatus], None]] = []
        
    def build_runner_command(self, preset: Optional[str] = None, scenario_path: Optional[Path] = None,
                           debug: bool = True, visualize: bool = False,
                           kpi_sm_revenue_rows: bool = False, kpi_sm_client_rows: bool = False) -> RunnerCommand:
        """Build a runner command for simulation execution.
        
        Args:
            preset: Preset scenario name
            scenario_path: Path to scenario file
            debug: Enable debug mode
            visualize: Generate visualizations
            kpi_sm_revenue_rows: Include SM revenue rows in KPI
            kpi_sm_client_rows: Include SM client rows in KPI
            
        Returns:
            RunnerCommand object
        """
        try:
            # Base command
            command = ["python", "simulate_growth.py"]
            
            # Add preset or scenario path
            if preset:
                command.extend(["--preset", preset])
            elif scenario_path:
                command.extend(["--scenario", str(scenario_path)])
            else:
                raise ValueError("Either preset or scenario_path must be provided")
            
            # Add optional flags
            if debug:
                command.append("--debug")
            
            if visualize:
                command.append("--visualize")
            
            if kpi_sm_revenue_rows:
                command.append("--kpi-sm-revenue-rows")
            
            if kpi_sm_client_rows:
                command.append("--kpi-sm-client-rows")
            
            # Set up environment
            env = {
                'PYTHONPATH': str(self.project_root),
                'PATH': self._get_python_path()
            }
            
            return RunnerCommand(command, self.project_root, env)
            
        except Exception as e:
            logger.error(f"Error building runner command: {e}")
            raise
    
    def start_simulation(self, command: RunnerCommand) -> Tuple[bool, Optional[str]]:
        """Start a simulation with the given command.
        
        Args:
            command: RunnerCommand to execute
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Stop any existing simulation
            self.stop_simulation()
            
            # Start the new simulation
            self.current_process = subprocess.Popen(
                command.command,
                cwd=command.working_dir,
                env={**command.env, **self._get_base_env()},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Update status
            self.current_status = RunnerStatus(
                process_id=self.current_process.pid,
                start_time=time.time()
            )
            self.current_status.is_running = True
            
            # Start log monitoring
            self._start_log_monitoring()
            
            # Update state manager
            self.state_manager.update_runner_state(is_running=True)
            
            logger.info(f"Started simulation with PID {self.current_process.pid}")
            return True, None
            
        except Exception as e:
            error_msg = f"Error starting simulation: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def stop_simulation(self) -> Tuple[bool, Optional[str]]:
        """Stop the currently running simulation.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if self.current_process and self.current_process.poll() is None:
                # Process is still running, terminate it
                self.current_process.terminate()
                
                # Wait for termination
                try:
                    self.current_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if termination takes too long
                    self.current_process.kill()
                    self.current_process.wait()
                
                logger.info("Simulation stopped")
            
            # Stop log monitoring
            self._stop_log_monitoring()
            
            # Update status
            if self.current_process:
                self.current_status.exit_code = self.current_process.returncode
            self.current_status.is_running = False
            
            # Update state manager
            self.state_manager.update_runner_state(is_running=False)
            
            return True, None
            
        except Exception as e:
            error_msg = f"Error stopping simulation: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_simulation_status(self) -> RunnerStatus:
        """Get the current simulation status.
        
        Returns:
            Current RunnerStatus
        """
        if self.current_process:
            # Update status from process
            self.current_status.is_running = self.current_process.poll() is None
            if not self.current_status.is_running:
                self.current_status.exit_code = self.current_process.returncode
        
        return self.current_status
    
    def add_status_callback(self, callback: Callable[[RunnerStatus], None]) -> None:
        """Add a callback for status updates.
        
        Args:
            callback: Function to call when status changes
        """
        self._status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable[[RunnerStatus], None]) -> None:
        """Remove a status callback.
        
        Args:
            callback: Function to remove
        """
        try:
            self._status_callbacks.remove(callback)
        except ValueError:
            pass
    
    def _start_log_monitoring(self) -> None:
        """Start monitoring simulation logs."""
        if self._log_monitor_thread and self._log_monitor_thread.is_alive():
            return
        
        self._stop_monitoring = False
        self._log_monitor_thread = threading.Thread(target=self._monitor_logs, daemon=True)
        self._log_monitor_thread.start()
    
    def _stop_log_monitoring(self) -> None:
        """Stop monitoring simulation logs."""
        self._stop_monitoring = True
        if self._log_monitor_thread:
            self._log_monitor_thread.join(timeout=5)
    
    def _monitor_logs(self) -> None:
        """Monitor simulation logs in a separate thread."""
        try:
            while not self._stop_monitoring and self.current_process:
                if self.current_process.poll() is not None:
                    # Process has finished
                    break
                
                # Read available output
                if self.current_process.stdout:
                    line = self.current_process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:
                            self.current_status.log_lines.append(line)
                            self.current_status.last_log_update = time.time()
                            
                            # Parse progress information
                            self._parse_progress(line)
                            
                            # Notify callbacks
                            self._notify_status_callbacks()
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
            
            # Final status update
            if self.current_process:
                self.current_status.exit_code = self.current_process.returncode
                self.current_status.is_running = False
                self._notify_status_callbacks()
                
        except Exception as e:
            logger.error(f"Error monitoring logs: {e}")
            self.current_status.error_message = str(e)
            self._notify_status_callbacks()
    
    def _parse_progress(self, line: str) -> None:
        """Parse progress information from log line.
        
        Args:
            line: Log line to parse
        """
        try:
            # Look for progress indicators in the log line
            if "step" in line.lower() and "of" in line.lower():
                # Extract step information
                import re
                step_match = re.search(r'step\s+(\d+)\s+of\s+(\d+)', line.lower())
                if step_match:
                    current_step = int(step_match.group(1))
                    total_steps = int(step_match.group(2))
                    if total_steps > 0:
                        self.current_status.progress = current_step / total_steps
                        self.current_status.current_step = f"Step {current_step}/{total_steps}"
            
            elif "time" in line.lower() and "=" in line:
                # Extract time information
                import re
                time_match = re.search(r'time\s*=\s*([\d.]+)', line.lower())
                if time_match:
                    current_time = float(time_match.group(1))
                    # Calculate progress based on time if we have time bounds
                    state = self.state_manager.get_state()
                    start_time = state.runspecs.starttime
                    stop_time = state.runspecs.stoptime
                    if stop_time > start_time:
                        self.current_status.progress = (current_time - start_time) / (stop_time - start_time)
                        self.current_status.current_step = f"Time: {current_time:.2f}"
                        
        except Exception as e:
            logger.debug(f"Error parsing progress from line '{line}': {e}")
    
    def _notify_status_callbacks(self) -> None:
        """Notify all status callbacks."""
        for callback in self._status_callbacks:
            try:
                callback(self.current_status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def get_latest_results(self) -> Optional[Path]:
        """Get the path to the latest results file.
        
        Returns:
            Path to latest results file or None if not found
        """
        try:
            output_dir = self.project_root / "output"
            if not output_dir.exists():
                return None
            
            # Look for CSV files
            csv_files = list(output_dir.glob("*.csv"))
            if not csv_files:
                return None
            
            # Return the most recently modified file
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            return latest_file
            
        except Exception as e:
            logger.error(f"Error finding latest results: {e}")
            return None
    
    def get_latest_plots(self) -> List[Path]:
        """Get the paths to the latest plot files.
        
        Returns:
            List of paths to plot files
        """
        try:
            plots_dir = self.project_root / "output" / "plots"
            if not plots_dir.exists():
                return []
            
            # Look for PNG files
            png_files = list(plots_dir.glob("*.png"))
            return sorted(png_files, key=lambda f: f.stat().st_mtime, reverse=True)
            
        except Exception as e:
            logger.error(f"Error finding latest plots: {e}")
            return []
    
    def read_log_file(self, max_lines: int = 1000) -> List[str]:
        """Read the simulation log file.
        
        Args:
            max_lines: Maximum number of lines to read
            
        Returns:
            List of log lines
        """
        try:
            log_file = self.project_root / "logs" / "run.log"
            if not log_file.exists():
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Return the last max_lines
                return [line.strip() for line in lines[-max_lines:] if line.strip()]
                
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return []
    
    def run_preset(self, preset: str, debug: bool = True, visualize: bool = False,
                  kpi_sm_revenue_rows: bool = False, kpi_sm_client_rows: bool = False) -> Tuple[bool, Optional[str]]:
        """Run a simulation using a preset scenario.
        
        Args:
            preset: Preset scenario name
            debug: Enable debug mode
            visualize: Generate visualizations
            kpi_sm_revenue_rows: Include SM revenue rows in KPI
            kpi_sm_client_rows: Include SM client rows in KPI
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Build command
            command = self.build_runner_command(
                preset=preset,
                debug=debug,
                visualize=visualize,
                kpi_sm_revenue_rows=kpi_sm_revenue_rows,
                kpi_sm_client_rows=kpi_sm_client_rows
            )
            
            # Start simulation
            return self.start_simulation(command)
            
        except Exception as e:
            error_msg = f"Error running preset '{preset}': {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def run_current_scenario(self, debug: bool = True, visualize: bool = False,
                           kpi_sm_revenue_rows: bool = False, kpi_sm_client_rows: bool = False) -> Tuple[bool, Optional[str]]:
        """Run a simulation using the current scenario state.
        
        Args:
            debug: Enable debug mode
            visualize: Generate visualizations
            kpi_sm_revenue_rows: Include SM revenue rows in KPI
            kpi_sm_client_rows: Include SM client rows in KPI
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Save current state to temporary scenario file
            scenario_data = self.state_manager.to_scenario_dict_normalized()
            temp_scenario_path = self.project_root / "scenarios" / f"temp_{int(time.time())}.yaml"
            
            with open(temp_scenario_path, 'w', encoding='utf-8') as f:
                yaml.dump(scenario_data, f, default_flow_style=False, sort_keys=False)
            
            # Build command
            command = self.build_runner_command(
                scenario_path=temp_scenario_path,
                debug=debug,
                visualize=visualize,
                kpi_sm_revenue_rows=kpi_sm_revenue_rows,
                kpi_sm_client_rows=kpi_sm_client_rows
            )
            
            # Start simulation
            success, error = self.start_simulation(command)
            
            # Clean up temporary file after a delay
            def cleanup_temp_file():
                time.sleep(5)  # Wait for simulation to start
                try:
                    if temp_scenario_path.exists():
                        temp_scenario_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not clean up temporary scenario file: {e}")
            
            cleanup_thread = threading.Thread(target=cleanup_temp_file, daemon=True)
            cleanup_thread.start()
            
            return success, error
            
        except Exception as e:
            error_msg = f"Error running current scenario: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _get_python_path(self) -> str:
        """Get the Python executable path.
        
        Returns:
            Python executable path
        """
        import sys
        return sys.executable
    
    def _get_base_env(self) -> Dict[str, str]:
        """Get base environment variables.
        
        Returns:
            Base environment variables
        """
        import os
        env = os.environ.copy()
        
        # Add project-specific environment variables
        env.update({
            'PYTHONPATH': str(self.project_root),
            'GROWTH_MODEL_ROOT': str(self.project_root),
        })
        
        return env
