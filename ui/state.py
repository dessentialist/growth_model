from __future__ import annotations

"""
Typed UI state models for the Streamlit GUI.

This module defines minimal, decoupled dataclasses that hold the current UI
scenario being edited: runspecs, constants overrides, and points (lookup) overrides.

The functions in this module are pure helpers for translating UI state to a
scenario dict compatible with `src.scenario_loader.validate_scenario_dict`.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional


@dataclass
class RunspecsState:
    """Runspecs fields with safe defaults.

    - starttime, stoptime, and dt are floats in year units
    - anchor_mode controls sector vs SM behavior. For Phases 3–5 we default to
      'sector' and allow switching to 'sm' to preview permissible keys.
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
    """Represents a proposed mapping of a single product to a sector with a start year.

    The UI captures proposed replacements to the primary product map on a per-sector basis.
    Each entry pairs a `product` with its `start_year`.
    """

    product: str
    start_year: float


@dataclass
class PrimaryMapState:
    """Holds proposed primary map replacements per sector.

    Structure mirrors the scenario schema expected by the backend validator:
    overrides.primary_map: { <sector>: [ { product: <str>, start_year: <float> }, ... ] }
    """

    by_sector: Dict[str, List[PrimaryMapEntry]] = field(default_factory=dict)


@dataclass
class SeedsState:
    """Holds seeding configuration for the scenario.

    - active_anchor_clients: number of ACTIVE anchor agents at t0 per sector
    - elapsed_quarters: optional aging per sector in quarters
    - direct_clients: number of direct clients per product at t0
    - active_anchor_clients_sm: SM-mode seeds per (sector, product)
    - completed_projects: sector-mode backlog of completed projects at t0
    - completed_projects_sm: SM-mode backlog per (sector, product)
    """

    active_anchor_clients: Dict[str, int] = field(default_factory=dict)
    elapsed_quarters: Dict[str, int] = field(default_factory=dict)
    direct_clients: Dict[str, int] = field(default_factory=dict)
    active_anchor_clients_sm: Dict[str, Dict[str, int]] = field(default_factory=dict)
    completed_projects: Dict[str, int] = field(default_factory=dict)
    completed_projects_sm: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class UIState:
    """Aggregate UI state for the scenario under construction."""

    name: str = "working_scenario"
    runspecs: RunspecsState = field(default_factory=RunspecsState)
    overrides: ScenarioOverridesState = field(default_factory=ScenarioOverridesState)
    primary_map: PrimaryMapState = field(default_factory=PrimaryMapState)
    seeds: SeedsState = field(default_factory=SeedsState)

    def to_scenario_dict(self) -> dict:
        """Translate to a plain dict expected by scenario validation.

        For Phases 6–8, we include runspecs, overrides (constants, points, primary_map)
        and seeds blocks. Points are returned as-is (may contain tuples), while
        `to_scenario_dict_normalized` ensures lists for serialization.
        """
        pm_block: Optional[Dict[str, List[Dict[str, float]]]] = None
        if self.primary_map.by_sector:
            pm_block = {}
            for sector, entries in self.primary_map.by_sector.items():
                pm_block[sector] = [{"product": e.product, "start_year": float(e.start_year)} for e in entries]

        seeds_block: Optional[dict] = None
        if (
            self.seeds.active_anchor_clients
            or self.seeds.elapsed_quarters
            or self.seeds.direct_clients
            or self.seeds.active_anchor_clients_sm
            or self.seeds.completed_projects
            or self.seeds.completed_projects_sm
        ):
            seeds_block = {}
            if self.seeds.active_anchor_clients:
                seeds_block["active_anchor_clients"] = dict(self.seeds.active_anchor_clients)
            if self.seeds.elapsed_quarters:
                seeds_block["elapsed_quarters"] = dict(self.seeds.elapsed_quarters)
            if self.seeds.direct_clients:
                seeds_block["direct_clients"] = dict(self.seeds.direct_clients)
            if self.seeds.active_anchor_clients_sm:
                seeds_block["active_anchor_clients_sm"] = {
                    s: dict(mmap) for s, mmap in self.seeds.active_anchor_clients_sm.items()
                }
            if self.seeds.completed_projects:
                seeds_block["completed_projects"] = dict(self.seeds.completed_projects)
            if self.seeds.completed_projects_sm:
                seeds_block["completed_projects_sm"] = {s: dict(mmap) for s, mmap in self.seeds.completed_projects_sm.items()}

        overrides_block: dict = {
            "constants": dict(self.overrides.constants),
            # Points omitted here; use normalized variant for serialization
        }
        if pm_block:
            overrides_block["primary_map"] = pm_block

        out: dict = {
            "name": self.name,
            "runspecs": asdict(self.runspecs),
            "overrides": overrides_block,
        }
        if seeds_block:
            out["seeds"] = seeds_block
        return out

    def to_scenario_dict_normalized(self) -> dict:
        """Assemble a scenario dict with normalized points as lists, not tuples."""
        points_map: Dict[str, List[List[float]]] = {}
        for name, series in self.overrides.points.items():
            # Ensure list-of-lists shape for YAML/JSON dumps and validation
            points_map[name] = [[float(t), float(v)] for (t, v) in series]
        # Start from non-normalized dict to include optional blocks
        base = self.to_scenario_dict()
        overrides_block = dict(base.get("overrides", {}))
        overrides_block["points"] = points_map
        base["overrides"] = overrides_block
        return base

    def load_from_scenario_dict(self, data: dict) -> None:
        """Load state from a scenario dict produced by loader or YAML.

        This function mutates the current instance to reflect the provided
        scenario. Unknown fields are ignored; missing fields retain defaults.
        """
        if not isinstance(data, dict):
            return
        # Name
        self.name = str(data.get("name") or self.name)
        # Runspecs
        rs = data.get("runspecs") or {}
        try:
            self.runspecs.starttime = float(rs.get("starttime", self.runspecs.starttime))
            self.runspecs.stoptime = float(rs.get("stoptime", self.runspecs.stoptime))
            self.runspecs.dt = float(rs.get("dt", self.runspecs.dt))
            mode = str(rs.get("anchor_mode", self.runspecs.anchor_mode)).strip().lower()
            if mode in {"sector", "sm"}:
                self.runspecs.anchor_mode = mode
        except Exception:
            pass
        # Overrides.constants
        ov = data.get("overrides") or {}
        consts = ov.get("constants") or {}
        if isinstance(consts, dict):
            self.overrides.constants = {str(k): float(v) for k, v in consts.items()}
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
            self.overrides.points = norm_points
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
            self.primary_map.by_sector = by_sector
        # Seeds
        seeds = data.get("seeds") or {}
        if isinstance(seeds, dict):
            aac = seeds.get("active_anchor_clients") or {}
            if isinstance(aac, dict):
                self.seeds.active_anchor_clients = {str(k): int(v) for k, v in aac.items() if int(v) > 0}
            eq = seeds.get("elapsed_quarters") or {}
            if isinstance(eq, dict):
                self.seeds.elapsed_quarters = {str(k): int(v) for k, v in eq.items() if int(v) > 0}
            dc = seeds.get("direct_clients") or {}
            if isinstance(dc, dict):
                self.seeds.direct_clients = {str(k): int(v) for k, v in dc.items() if int(v) > 0}
            sm = seeds.get("active_anchor_clients_sm") or {}
            if isinstance(sm, dict):
                norm_sm: Dict[str, Dict[str, int]] = {}
                for s, mmap in sm.items():
                    if isinstance(mmap, dict):
                        mm = {str(m): int(v) for m, v in mmap.items() if int(v) > 0}
                        if mm:
                            norm_sm[str(s)] = mm
                self.seeds.active_anchor_clients_sm = norm_sm
            cp = seeds.get("completed_projects") or {}
            if isinstance(cp, dict):
                self.seeds.completed_projects = {str(k): int(v) for k, v in cp.items() if int(v) > 0}
            cpsm = seeds.get("completed_projects_sm") or {}
            if isinstance(cpsm, dict):
                norm_cpsm: Dict[str, Dict[str, int]] = {}
                for s, mmap in cpsm.items():
                    if isinstance(mmap, dict):
                        mm = {str(m): int(v) for m, v in mmap.items() if int(v) > 0}
                        if mm:
                            norm_cpsm[str(s)] = mm
                self.seeds.completed_projects_sm = norm_cpsm


__all__ = [
    "RunspecsState",
    "ScenarioOverridesState",
    "PrimaryMapEntry",
    "PrimaryMapState",
    "SeedsState",
    "UIState",
]
