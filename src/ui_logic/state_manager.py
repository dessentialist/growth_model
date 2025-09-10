"""
Framework-agnostic state management for the Growth Model UI.

This module provides reactive state management that can be used by any UI framework.
It handles all application state including scenarios, runspecs, overrides, and UI state.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional, Any, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TabType(Enum):
    """Enumeration of available tabs in the application."""
    RUNNER = "runner"
    MAPPING = "mapping" 
    LOGS = "logs"
    OUTPUT = "output"
    PARAMETERS = "parameters"
    POINTS = "points"
    SEEDS = "seeds"


@dataclass
class RunspecsState:
    """Runspecs configuration with safe defaults.
    
    - starttime, stoptime, and dt are floats in year units
    - anchor_mode controls sector vs SM behavior
    """
    starttime: float = 2025.0
    stoptime: float = 2032.0
    dt: float = 0.25
    anchor_mode: str = "sector"


@dataclass
class ScenarioOverridesState:
    """Holds override maps for constants and points (lookups).
    
    - constants: mapping of element name -> numeric value
    - points: mapping of lookup name -> list of [time, value] numeric pairs
    """
    constants: Dict[str, float] = field(default_factory=dict)
    points: Dict[str, List[Tuple[float, float]]] = field(default_factory=dict)


@dataclass
class PrimaryMapEntry:
    """Represents a mapping of a single product to a sector with a start year."""
    product: str
    start_year: float


@dataclass
class PrimaryMapState:
    """Holds proposed primary map replacements per sector."""
    by_sector: Dict[str, List[PrimaryMapEntry]] = field(default_factory=dict)


@dataclass
class SeedsState:
    """Holds seeding configuration for the scenario."""
    active_anchor_clients: Dict[str, int] = field(default_factory=dict)
    elapsed_quarters: Dict[str, int] = field(default_factory=dict)
    direct_clients: Dict[str, int] = field(default_factory=dict)
    active_anchor_clients_sm: Dict[str, Dict[str, int]] = field(default_factory=dict)
    elapsed_quarters_sm: Dict[str, Dict[str, int]] = field(default_factory=dict)
    completed_projects: Dict[str, int] = field(default_factory=dict)
    completed_projects_sm: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class RunnerState:
    """State for the runner tab and execution controls."""
    is_running: bool = False
    current_preset: str = "baseline"
    debug_mode: bool = True
    visualize: bool = False
    kpi_sm_revenue_rows: bool = False
    kpi_sm_client_rows: bool = False
    last_run_exit_code: Optional[int] = None
    last_run_logs: List[str] = field(default_factory=list)
    last_results_path: Optional[str] = None


@dataclass
class LogsState:
    """State for the logs tab."""
    log_lines: List[str] = field(default_factory=list)
    log_level: str = "INFO"
    auto_refresh: bool = True
    filter_text: str = ""


@dataclass
class OutputState:
    """State for the output tab."""
    results_data: Optional[Any] = None  # DataFrame or similar
    plots_available: List[str] = field(default_factory=list)
    selected_plot: Optional[str] = None
    export_format: str = "csv"


@dataclass
class UIState:
    """Aggregate UI state for the entire application."""
    name: str = "working_scenario"
    active_tab: TabType = TabType.RUNNER
    runspecs: RunspecsState = field(default_factory=RunspecsState)
    overrides: ScenarioOverridesState = field(default_factory=ScenarioOverridesState)
    primary_map: PrimaryMapState = field(default_factory=PrimaryMapState)
    seeds: SeedsState = field(default_factory=SeedsState)
    runner: RunnerState = field(default_factory=RunnerState)
    logs: LogsState = field(default_factory=LogsState)
    output: OutputState = field(default_factory=OutputState)


class StateManager:
    """
    Framework-agnostic state manager with reactive patterns.
    
    This class manages all application state and provides reactive updates
    through callback mechanisms that can be implemented by any UI framework.
    """
    
    def __init__(self):
        """Initialize the state manager with default state."""
        self._state = UIState()
        self._listeners: Dict[str, List[Callable]] = {}
        self._history: List[UIState] = []
        self._max_history = 50
        
    def get_state(self) -> UIState:
        """Get the current application state."""
        return self._state
    
    def set_state(self, new_state: UIState) -> None:
        """Set the entire application state and notify listeners."""
        old_state = self._state
        self._state = new_state
        
        # Add to history
        self._history.append(old_state)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Notify all listeners
        self._notify_listeners("state_changed", old_state, new_state)
        
    def update_state(self, **kwargs) -> None:
        """Update specific parts of the state."""
        current_state = self._state
        new_state = UIState(
            name=kwargs.get("name", current_state.name),
            active_tab=kwargs.get("active_tab", current_state.active_tab),
            runspecs=kwargs.get("runspecs", current_state.runspecs),
            overrides=kwargs.get("overrides", current_state.overrides),
            primary_map=kwargs.get("primary_map", current_state.primary_map),
            seeds=kwargs.get("seeds", current_state.seeds),
            runner=kwargs.get("runner", current_state.runner),
            logs=kwargs.get("logs", current_state.logs),
            output=kwargs.get("output", current_state.output),
        )
        self.set_state(new_state)
    
    def update_runspecs(self, **kwargs) -> None:
        """Update runspecs state."""
        current_runspecs = self._state.runspecs
        new_runspecs = RunspecsState(
            starttime=kwargs.get("starttime", current_runspecs.starttime),
            stoptime=kwargs.get("stoptime", current_runspecs.stoptime),
            dt=kwargs.get("dt", current_runspecs.dt),
            anchor_mode=kwargs.get("anchor_mode", current_runspecs.anchor_mode),
        )
        self.update_state(runspecs=new_runspecs)
    
    def update_overrides(self, **kwargs) -> None:
        """Update scenario overrides state."""
        current_overrides = self._state.overrides
        new_overrides = ScenarioOverridesState(
            constants=kwargs.get("constants", current_overrides.constants),
            points=kwargs.get("points", current_overrides.points),
        )
        self.update_state(overrides=new_overrides)
    
    def update_primary_map(self, **kwargs) -> None:
        """Update primary map state."""
        current_map = self._state.primary_map
        new_map = PrimaryMapState(
            by_sector=kwargs.get("by_sector", current_map.by_sector),
        )
        self.update_state(primary_map=new_map)
    
    def update_seeds(self, **kwargs) -> None:
        """Update seeds state."""
        current_seeds = self._state.seeds
        new_seeds = SeedsState(
            active_anchor_clients=kwargs.get("active_anchor_clients", current_seeds.active_anchor_clients),
            elapsed_quarters=kwargs.get("elapsed_quarters", current_seeds.elapsed_quarters),
            direct_clients=kwargs.get("direct_clients", current_seeds.direct_clients),
            active_anchor_clients_sm=kwargs.get("active_anchor_clients_sm", current_seeds.active_anchor_clients_sm),
            completed_projects=kwargs.get("completed_projects", current_seeds.completed_projects),
            completed_projects_sm=kwargs.get("completed_projects_sm", current_seeds.completed_projects_sm),
        )
        self.update_state(seeds=new_seeds)
    
    def update_runner_state(self, **kwargs) -> None:
        """Update runner state."""
        current_runner = self._state.runner
        new_runner = RunnerState(
            is_running=kwargs.get("is_running", current_runner.is_running),
            current_preset=kwargs.get("current_preset", current_runner.current_preset),
            debug_mode=kwargs.get("debug_mode", current_runner.debug_mode),
            visualize=kwargs.get("visualize", current_runner.visualize),
            kpi_sm_revenue_rows=kwargs.get("kpi_sm_revenue_rows", current_runner.kpi_sm_revenue_rows),
            kpi_sm_client_rows=kwargs.get("kpi_sm_client_rows", current_runner.kpi_sm_client_rows),
            last_run_exit_code=kwargs.get("last_run_exit_code", current_runner.last_run_exit_code),
            last_run_logs=kwargs.get("last_run_logs", current_runner.last_run_logs),
            last_results_path=kwargs.get("last_results_path", current_runner.last_results_path),
        )
        self.update_state(runner=new_runner)
    
    def update_logs_state(self, **kwargs) -> None:
        """Update logs state."""
        current_logs = self._state.logs
        new_logs = LogsState(
            log_lines=kwargs.get("log_lines", current_logs.log_lines),
            log_level=kwargs.get("log_level", current_logs.log_level),
            auto_refresh=kwargs.get("auto_refresh", current_logs.auto_refresh),
            filter_text=kwargs.get("filter_text", current_logs.filter_text),
        )
        self.update_state(logs=new_logs)
    
    def update_output_state(self, **kwargs) -> None:
        """Update output state."""
        current_output = self._state.output
        new_output = OutputState(
            results_data=kwargs.get("results_data", current_output.results_data),
            plots_available=kwargs.get("plots_available", current_output.plots_available),
            selected_plot=kwargs.get("selected_plot", current_output.selected_plot),
            export_format=kwargs.get("export_format", current_output.export_format),
        )
        self.update_state(output=new_output)
    
    def set_active_tab(self, tab: TabType) -> None:
        """Set the active tab."""
        self.update_state(active_tab=tab)
    
    def add_listener(self, event: str, callback: Callable) -> None:
        """Add a listener for state change events."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
    
    def remove_listener(self, event: str, callback: Callable) -> None:
        """Remove a listener for state change events."""
        if event in self._listeners:
            try:
                self._listeners[event].remove(callback)
            except ValueError:
                pass
    
    def _notify_listeners(self, event: str, *args, **kwargs) -> None:
        """Notify all listeners for a specific event."""
        if event in self._listeners:
            for callback in self._listeners[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in state listener callback: {e}")
    
    def undo(self) -> bool:
        """Undo the last state change if possible."""
        if self._history:
            previous_state = self._history.pop()
            self._state = previous_state
            self._notify_listeners("state_changed", self._state, self._state)
            return True
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self._history) > 0
    
    def to_scenario_dict(self) -> dict:
        """Convert current state to scenario dictionary format."""
        pm_block: Optional[Dict[str, List[Dict[str, float]]]] = None
        if self._state.primary_map.by_sector:
            pm_block = {}
            for sector, entries in self._state.primary_map.by_sector.items():
                pm_block[sector] = [{"product": e.product, "start_year": float(e.start_year)} for e in entries]

        seeds_block: Optional[dict] = None
        if (
            self._state.seeds.active_anchor_clients
            or self._state.seeds.elapsed_quarters
            or self._state.seeds.direct_clients
            or self._state.seeds.active_anchor_clients_sm
            or self._state.seeds.elapsed_quarters_sm
            or self._state.seeds.completed_projects
            or self._state.seeds.completed_projects_sm
        ):
            seeds_block = {}
            if self._state.seeds.active_anchor_clients:
                seeds_block["active_anchor_clients"] = dict(self._state.seeds.active_anchor_clients)
            if self._state.seeds.elapsed_quarters:
                seeds_block["elapsed_quarters"] = dict(self._state.seeds.elapsed_quarters)
            if self._state.seeds.direct_clients:
                seeds_block["direct_clients"] = dict(self._state.seeds.direct_clients)
            if self._state.seeds.active_anchor_clients_sm:
                seeds_block["active_anchor_clients_sm"] = {
                    s: dict(mmap) for s, mmap in self._state.seeds.active_anchor_clients_sm.items()
                }
            if self._state.seeds.elapsed_quarters_sm:
                seeds_block["elapsed_quarters_sm"] = {
                    s: dict(mmap) for s, mmap in self._state.seeds.elapsed_quarters_sm.items()
                }
            if self._state.seeds.completed_projects:
                seeds_block["completed_projects"] = dict(self._state.seeds.completed_projects)
            if self._state.seeds.completed_projects_sm:
                seeds_block["completed_projects_sm"] = {
                    s: dict(mmap) for s, mmap in self._state.seeds.completed_projects_sm.items()
                }

        overrides_block: dict = {
            "constants": dict(self._state.overrides.constants),
        }
        if pm_block:
            overrides_block["primary_map"] = pm_block

        out: dict = {
            "name": self._state.name,
            "runspecs": asdict(self._state.runspecs),
            "overrides": overrides_block,
        }
        if seeds_block:
            out["seeds"] = seeds_block
        return out

    def to_scenario_dict_normalized(self) -> dict:
        """Convert current state to normalized scenario dictionary format."""
        points_map: Dict[str, List[List[float]]] = {}
        for name, series in self._state.overrides.points.items():
            # Ensure list-of-lists shape for YAML/JSON dumps and validation
            points_map[name] = [[float(t), float(v)] for (t, v) in series]
        
        # Start from non-normalized dict to include optional blocks
        base = self.to_scenario_dict()
        overrides_block = dict(base.get("overrides", {}))
        overrides_block["points"] = points_map
        base["overrides"] = overrides_block
        return base

    def load_from_scenario_dict(self, data: dict) -> None:
        """Load state from a scenario dictionary."""
        if not isinstance(data, dict):
            return
            
        # Name
        self._state.name = str(data.get("name") or self._state.name)
        
        # Runspecs
        rs = data.get("runspecs") or {}
        try:
            new_runspecs = RunspecsState(
                starttime=float(rs.get("starttime", self._state.runspecs.starttime)),
                stoptime=float(rs.get("stoptime", self._state.runspecs.stoptime)),
                dt=float(rs.get("dt", self._state.runspecs.dt)),
                anchor_mode=str(rs.get("anchor_mode", self._state.runspecs.anchor_mode)).strip().lower(),
            )
            self.update_state(runspecs=new_runspecs)
        except Exception as e:
            logger.error(f"Error loading runspecs: {e}")
        
        # Overrides.constants
        ov = data.get("overrides") or {}
        consts = ov.get("constants") or {}
        if isinstance(consts, dict):
            new_constants = {str(k): float(v) for k, v in consts.items()}
            self.update_overrides(constants=new_constants)
        
        # Overrides.points
        points = ov.get("points") or {}
        if isinstance(points, dict):
            norm_points: Dict[str, List[Tuple[float, float]]] = {}
            for name, series in points.items():
                rows: List[Tuple[float, float]] = []
                if isinstance(series, list):
                    for pair in series:
                        if isinstance(pair, (list, tuple)) and len(pair) == 2:
                            try:
                                rows.append((float(pair[0]), float(pair[1])))
                            except Exception:
                                continue
                if rows:
                    rows.sort(key=lambda x: x[0])
                    norm_points[str(name)] = rows
            self.update_overrides(points=norm_points)
        
        # Overrides.primary_map
        pm = ov.get("primary_map") or {}
        if isinstance(pm, dict):
            by_sector: Dict[str, List[PrimaryMapEntry]] = {}
            for s, entries in pm.items():
                if isinstance(entries, list):
                    ll: List[PrimaryMapEntry] = []
                    for e in entries:
                        if isinstance(e, dict):
                            prod = str(e.get("product", "")).strip()
                            sy = e.get("start_year", 2025.0)
                            try:
                                syf = float(sy)
                            except Exception:
                                syf = 2025.0
                            if prod:
                                ll.append(PrimaryMapEntry(product=prod, start_year=syf))
                    if ll:
                        by_sector[str(s)] = sorted(ll, key=lambda x: x.product)
            self.update_primary_map(by_sector=by_sector)
        
        # Seeds
        seeds = data.get("seeds") or {}
        if isinstance(seeds, dict):
            new_seeds = SeedsState()
            
            aac = seeds.get("active_anchor_clients") or {}
            if isinstance(aac, dict):
                new_seeds.active_anchor_clients = {str(k): int(v) for k, v in aac.items() if int(v) > 0}
            
            eq = seeds.get("elapsed_quarters") or {}
            if isinstance(eq, dict):
                new_seeds.elapsed_quarters = {str(k): int(v) for k, v in eq.items() if int(v) > 0}
            
            dc = seeds.get("direct_clients") or {}
            if isinstance(dc, dict):
                new_seeds.direct_clients = {str(k): int(v) for k, v in dc.items() if int(v) > 0}
            
            sm = seeds.get("active_anchor_clients_sm") or {}
            if isinstance(sm, dict):
                norm_sm: Dict[str, Dict[str, int]] = {}
                for s, mmap in sm.items():
                    if isinstance(mmap, dict):
                        mm = {str(m): int(v) for m, v in mmap.items() if int(v) > 0}
                        if mm:
                            norm_sm[str(s)] = mm
                new_seeds.active_anchor_clients_sm = norm_sm
            
            eqsm = seeds.get("elapsed_quarters_sm") or {}
            if isinstance(eqsm, dict):
                norm_eqsm: Dict[str, Dict[str, int]] = {}
                for s, mmap in eqsm.items():
                    if isinstance(mmap, dict):
                        mm = {str(m): int(v) for m, v in mmap.items() if int(v) > 0}
                        if mm:
                            norm_eqsm[str(s)] = mm
                new_seeds.elapsed_quarters_sm = norm_eqsm
            
            cp = seeds.get("completed_projects") or {}
            if isinstance(cp, dict):
                new_seeds.completed_projects = {str(k): int(v) for k, v in cp.items() if int(v) > 0}
            
            cpsm = seeds.get("completed_projects_sm") or {}
            if isinstance(cpsm, dict):
                norm_cpsm: Dict[str, Dict[str, int]] = {}
                for s, mmap in cpsm.items():
                    if isinstance(mmap, dict):
                        mm = {str(m): int(v) for m, v in mmap.items() if int(v) > 0}
                        if mm:
                            norm_cpsm[str(s)] = mm
                new_seeds.completed_projects_sm = norm_cpsm
            
            self.update_state(seeds=new_seeds)
