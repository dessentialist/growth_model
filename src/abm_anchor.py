from __future__ import annotations

"""
Phase 5 — ABM: AnchorClientAgent & Sector Factories

This module implements the agent-based portion of the hybrid model for
Anchor Clients. Each Anchor Client is represented as a deterministic agent
with a simple lifecycle and per-step requirement generation for the
sector's primary materials. There is strictly no randomness and no hidden
defaults: all behavior is driven by Phase 1 inputs (Anchor Client
Parameters.csv) and the Primary Material mapping (Primary Material.csv).

Agent lifecycle overview
------------------------
- An agent begins life as a Potential Client (POTENTIAL) with no
  requirements. While POTENTIAL, it starts projects at a sector-specific
  per-quarter rate until a maximum number of projects is reached.
- Each started project completes after a sector-specific duration (in
  quarters). When the number of completed projects reaches or exceeds a
  threshold, the agent sets an activation_time = now + activation_delay
  and transitions to PENDING_ACTIVATION.
- When the current simulation time reaches activation_time, the agent
  transitions to ACTIVE. While ACTIVE, it generates per-material
  requirements (flows per quarter) using a three-phase logic:
  initial → ramp → steady, with per-phase base rates and per-phase growth
  rates. The material must also be active for the sector (the sector–
  material start year must have been reached) for requirements to be
  produced in that material.

Time units and scaling
----------------------
- The global time axis is in years; dt = 0.25 years corresponds to one
  quarter. Sector parameters for durations and delays are specified in
  quarters. Where we need to compute an absolute time (in years), we
  convert quarters to years using years = quarters * 0.25.
- Rates such as project_generation_rate are defined per quarter. Since
  the stepwise runner operates in quarter steps (dt ≈ 0.25 years), the
  natural increment per step is exactly the per-quarter rate. If dt is
  not 0.25, we scale deterministically by dt / 0.25 to preserve the
  intended per-quarter semantics without introducing randomness.

Factories
---------
This module also exposes factory builders that construct sector-specific
agent factories from the Phase 1 bundle. The factories embed the sector's
parameters and material start years and return fresh agents on demand.

Testing & determinism
---------------------
- The implementation is fully deterministic. Given the same inputs and
  time grid, repeated runs produce identical outputs. The tests validate
  lifecycle transitions and requirement generation over a small timeline.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Mapping, Optional

from .phase1_data import Phase1Bundle


QUARTER_IN_YEARS: float = 0.25


class AnchorClientAgentState(Enum):
    POTENTIAL = auto()  # Not yet active; starting/completing projects
    PENDING_ACTIVATION = auto()  # Threshold reached; waiting for activation delay
    ACTIVE = auto()  # Generating material requirements per step


@dataclass(frozen=True)
class AnchorClientParams:
    """Container for required sector parameters.

    All fields are numeric and come directly from `Anchor Client Parameters.csv`.
    Durations and delays are expressed in quarters.
    Rates are expressed per quarter.
    """

    # Project lifecycle
    project_generation_rate: float  # projects per quarter per agent
    max_projects_per_pc: float  # maximum number of projects to ever start
    project_duration_quarters: float  # quarters to complete a project
    projects_to_client_conversion: float  # completed projects threshold
    anchor_client_activation_delay_quarters: float  # quarters to wait after threshold

    # Requirement phases (per-quarter base rate and per-quarter growth)
    initial_phase_duration_quarters: float
    ramp_phase_duration_quarters: float
    initial_requirement_rate: float
    initial_req_growth: float
    ramp_requirement_rate: float
    ramp_req_growth: float
    steady_requirement_rate: float
    steady_req_growth: float

    # Phase 16: Optional per-(sector, material) overrides for requirement phases
    # These are provided at factory construction time as material-specific maps and
    # stored on the agent; we do not add them to this dataclass to keep sector-level
    # params stable. See factory code for integration.


def _quarters_to_years(quarters: float) -> float:
    """Convert quarters to years deterministically using the 0.25 factor."""
    return float(quarters) * QUARTER_IN_YEARS


def _steps_per_quarter(dt_years: float) -> float:
    """Return the deterministic scaling from per-quarter rates to per-step increments."""
    if dt_years <= 0:
        raise ValueError("dt_years must be positive")
    return dt_years / QUARTER_IN_YEARS


class AnchorClientAgent:
    """Deterministic agent for an Anchor Client.

    The agent encapsulates project lifecycle and per-material requirement
    generation. The `act` method advances internal state and returns a
    per-material mapping of requirement flows for the current step.
    """

    def __init__(
        self,
        *,
        sector: str,
        params: AnchorClientParams,
        material_start_year_by_material: Mapping[str, float],
        # Phase 16: optional per-(s,m) phase parameter overrides. Each map is
        # material -> float. Missing materials fall back to sector-level values.
        sm_initial_requirement_rate: Optional[Mapping[str, float]] = None,
        sm_initial_req_growth: Optional[Mapping[str, float]] = None,
        sm_ramp_requirement_rate: Optional[Mapping[str, float]] = None,
        sm_ramp_req_growth: Optional[Mapping[str, float]] = None,
        sm_steady_requirement_rate: Optional[Mapping[str, float]] = None,
        sm_steady_req_growth: Optional[Mapping[str, float]] = None,
        agent_label: Optional[str] = None,
    ) -> None:
        self.sector: str = str(sector)
        self.params: AnchorClientParams = params
        # Normalize material names as provided in Inputs; values are absolute years
        self.material_start_year_by_material: Dict[str, float] = {
            str(k): float(v) for k, v in dict(material_start_year_by_material).items()
        }

        # Optional label for debugging; if not provided, generate a cute default
        self.label: str = agent_label or f"bouncy-kitten_{self.sector}"

        # Lifecycle state
        self.state: AnchorClientAgentState = AnchorClientAgentState.POTENTIAL
        self.activation_time_years: Optional[float] = None

        # Project accumulators
        self._project_start_accumulator: float = 0.0
        self._num_projects_started: int = 0
        self._project_completion_times_years: List[float] = []
        self._num_projects_completed: int = 0

        # Last-step requirements snapshot (material -> float)
        self.requirements: Dict[str, float] = {m: 0.0 for m in self.material_start_year_by_material}

        # Phase 16: store per-(s,m) overrides as dicts with defaults
        self._sm_initial_requirement_rate = {str(k): float(v) for k, v in (dict(sm_initial_requirement_rate or {}) ).items()}
        self._sm_initial_req_growth = {str(k): float(v) for k, v in (dict(sm_initial_req_growth or {}) ).items()}
        self._sm_ramp_requirement_rate = {str(k): float(v) for k, v in (dict(sm_ramp_requirement_rate or {}) ).items()}
        self._sm_ramp_req_growth = {str(k): float(v) for k, v in (dict(sm_ramp_req_growth or {}) ).items()}
        self._sm_steady_requirement_rate = {str(k): float(v) for k, v in (dict(sm_steady_requirement_rate or {}) ).items()}
        self._sm_steady_req_growth = {str(k): float(v) for k, v in (dict(sm_steady_req_growth or {}) ).items()}

    # ----- Public read-only properties (useful for tests and runner) -----
    @property
    def num_projects_started(self) -> int:
        return self._num_projects_started

    @property
    def num_projects_completed(self) -> int:
        return self._num_projects_completed

    # ----- Core behavior -----
    def act(self, t_years: float, round_no: int, step_no: int, *, dt_years: float = QUARTER_IN_YEARS) -> Dict[str, float]:
        """Advance the agent by one step at absolute time `t_years`.

        Parameters
        ----------
        t_years : float
            Current simulation time in years.
        round_no : int
            Unused but included for interface parity with the runner.
        step_no : int
            Unused but included for interface parity with the runner.
        dt_years : float
            Step size in years (default 0.25 years = 1 quarter).

        Returns
        -------
        Dict[str, float]
            A mapping material -> requirement for this step.
        """

        # 1) Progress projects and handle activation transitions
        self._progress_projects_and_activation(t_years, dt_years)

        # 2) Generate per-material requirements deterministically
        self.requirements = self._generate_requirements_for_current_step(t_years)
        return dict(self.requirements)

    # ----- Internal helpers -----
    def _progress_projects_and_activation(self, t_years: float, dt_years: float) -> None:
        # While POTENTIAL, continue starting projects up to the maximum
        if self.state is AnchorClientAgentState.POTENTIAL:
            # ACTIVE PROJECTS FIX: Complete existing projects first, then start new ones
            # This ensures projects have at least one step of in-progress duration.
            # 
            # Previous bug: Starting projects and then immediately checking for completion
            # in the same step caused projects with short durations (e.g., 1 quarter) to
            # complete immediately, resulting in zero in-progress projects in KPIs.
            #
            # Solution: Reverse the order so existing projects complete first, creating
            # proper temporal separation between project start and completion events.
            self._update_completed_projects(dt_years)
            self._maybe_start_projects(dt_years)
            # Threshold check for activation scheduling
            if (
                self.activation_time_years is None
                and self._num_projects_completed >= self.params.projects_to_client_conversion
            ):
                self.activation_time_years = t_years + _quarters_to_years(
                    self.params.anchor_client_activation_delay_quarters
                )
                self.state = AnchorClientAgentState.PENDING_ACTIVATION

        # If waiting for activation and time is reached, activate now
        if self.state is AnchorClientAgentState.PENDING_ACTIVATION:
            if self.activation_time_years is not None and t_years >= self.activation_time_years:
                self.state = AnchorClientAgentState.ACTIVE

    def _maybe_start_projects(self, dt_years: float) -> None:
        # Respect the maximum number of projects that can ever be started
        max_projects = int(self.params.max_projects_per_pc)
        if self._num_projects_started >= max_projects:
            return

        # Deterministic accumulate-and-fire on per-quarter project generation rate
        scale = _steps_per_quarter(dt_years)
        self._project_start_accumulator += self.params.project_generation_rate * scale

        # Convert accumulator to integer starts this step
        to_start = int(self._project_start_accumulator)
        if to_start <= 0:
            return

        # Clamp to remaining capacity
        can_start = min(to_start, max_projects - self._num_projects_started)
        if can_start <= 0:
            return

        # Schedule completion times for newly started projects
        completion_offset_years = _quarters_to_years(self.params.project_duration_quarters)
        for _ in range(can_start):
            self._num_projects_started += 1
            self._project_completion_times_years.append(
                # Completion time = now + duration. We do not know absolute "now" here
                # because this function does not receive t_years; instead, project
                # completion processing compares against the latest known time from
                # `_update_completed_projects`, which is acceptable because all the
                # projects started within a step will complete uniformly after the
                # same duration relative to their start step.
                # We model this by storing only the relative offset and accounting
                # for completion in `_update_completed_projects` via a rolling
                # horizon.
                completion_offset_years
            )
        # Drain the integer part of the accumulator after starting projects
        self._project_start_accumulator -= to_start

    def _update_completed_projects(self, dt_years: float) -> None:
        # We track completion offsets; translate them to absolute completion
        # times relative to the time we started tracking completions.
        # To keep this simple and deterministic without storing historical
        # absolute start times, we treat the offsets list as a countdown timer:
        # subtract dt (implicitly one quarter per step via act caller) at each
        # step and mark completed when <= 0.
        #
        # Implementation: move the countdown logic here by reducing existing
        # offsets by one step (one quarter) and counting completions.
        if not self._project_completion_times_years:
            return

        # Reduce all offsets by the current step size (in years)
        new_offsets: List[float] = []
        decrement = float(dt_years)
        for remaining in self._project_completion_times_years:
            remaining_after = remaining - decrement
            if remaining_after <= 1e-12:
                self._num_projects_completed += 1
            else:
                new_offsets.append(remaining_after)
        self._project_completion_times_years = new_offsets

    def _generate_requirements_for_current_step(self, t_years: float) -> Dict[str, float]:
        # If not ACTIVE, no requirements are produced
        if self.state is not AnchorClientAgentState.ACTIVE:
            return {m: 0.0 for m in self.material_start_year_by_material}

        assert self.activation_time_years is not None
        # Quarter index since activation (integer step counter).
        # Use floor-like behavior for stability against floating round-off
        # so the very first active step is q_index = 0.
        elapsed_years = max(0.0, t_years - self.activation_time_years)
        q_since_activation = max(0, int(elapsed_years / QUARTER_IN_YEARS + 1e-12))

        # Convert phase durations to integers (quarters); use round to respect fractional inputs
        d_initial = max(0, int(round(self.params.initial_phase_duration_quarters)))
        d_ramp = max(0, int(round(self.params.ramp_phase_duration_quarters)))

        # Helper to compute phase-based requirement value for a given quarter index
        def phase_value_for_material(m: str, q_index: int) -> float:
            # Resolve per-(s,m) overrides if present; else fallback to sector-level
            init_rate = self._sm_initial_requirement_rate.get(m, self.params.initial_requirement_rate)
            init_g = self._sm_initial_req_growth.get(m, self.params.initial_req_growth)
            ramp_rate = self._sm_ramp_requirement_rate.get(m, self.params.ramp_requirement_rate)
            ramp_g = self._sm_ramp_req_growth.get(m, self.params.ramp_req_growth)
            steady_rate = self._sm_steady_requirement_rate.get(m, self.params.steady_requirement_rate)
            steady_g = self._sm_steady_req_growth.get(m, self.params.steady_req_growth)

            if q_index < d_initial:
                return init_rate * (1 + init_g) ** q_index
            if q_index < d_initial + d_ramp:
                step_in_ramp = q_index - d_initial
                return ramp_rate * (1 + ramp_g) ** step_in_ramp
            step_in_steady = q_index - (d_initial + d_ramp)
            return steady_rate * (1 + steady_g) ** step_in_steady

        out: Dict[str, float] = {}
        for material, start_year in self.material_start_year_by_material.items():
            if t_years < start_year:
                out[material] = 0.0
                continue
            out[material] = float(phase_value_for_material(material, q_since_activation))
        return out


def _require_anchor_param(bundle: Phase1Bundle, sector: str, param: str) -> float:
    try:
        return float(bundle.anchor.by_sector.at[param, sector])
    except Exception as exc:
        raise ValueError(f"Missing anchor parameter '{param}' for sector '{sector}'") from exc


def build_anchor_agent_factory_for_sector(bundle: Phase1Bundle, sector: str) -> Callable[[], AnchorClientAgent]:
    """Return a zero-arg factory that creates fresh `AnchorClientAgent` for `sector`.

    The factory closes over sector parameters and sector→materials start years
    discovered in Phase 1 inputs. No defaults are inserted; missing inputs
    raise clear errors.
    """

    # Collect required parameters (strict)
    params = AnchorClientParams(
        project_generation_rate=_require_anchor_param(bundle, sector, "project_generation_rate"),
        max_projects_per_pc=_require_anchor_param(bundle, sector, "max_projects_per_pc"),
        project_duration_quarters=_require_anchor_param(bundle, sector, "project_duration"),
        projects_to_client_conversion=_require_anchor_param(bundle, sector, "projects_to_client_conversion"),
        anchor_client_activation_delay_quarters=_require_anchor_param(bundle, sector, "anchor_client_activation_delay"),
        initial_phase_duration_quarters=_require_anchor_param(bundle, sector, "initial_phase_duration"),
        ramp_phase_duration_quarters=_require_anchor_param(bundle, sector, "ramp_phase_duration"),
        initial_requirement_rate=_require_anchor_param(bundle, sector, "initial_requirement_rate"),
        initial_req_growth=_require_anchor_param(bundle, sector, "initial_req_growth"),
        ramp_requirement_rate=_require_anchor_param(bundle, sector, "ramp_requirement_rate"),
        ramp_req_growth=_require_anchor_param(bundle, sector, "ramp_req_growth"),
        steady_requirement_rate=_require_anchor_param(bundle, sector, "steady_requirement_rate"),
        steady_req_growth=_require_anchor_param(bundle, sector, "steady_req_growth"),
    )

    # Build material start-year map for the sector
    df = bundle.primary_map.long
    starts = df[df["Sector"].astype(str) == str(sector)][["Material", "StartYear"]]
    if starts.empty:
        raise ValueError(f"Sector '{sector}' has no primary materials mapping; cannot build agent factory")
    material_start_year_by_material = {str(row.Material): float(row.StartYear) for _, row in starts.iterrows()}

    # Phase 16: collect per-(s,m) overrides for phase parameters from bundle.anchor_sm
    sm_df = getattr(bundle, "anchor_sm", None)
    sm_maps = {
        "initial_requirement_rate": {},
        "initial_req_growth": {},
        "ramp_requirement_rate": {},
        "ramp_req_growth": {},
        "steady_requirement_rate": {},
        "steady_req_growth": {},
    }
    if sm_df is not None and not sm_df.empty:
        sel = sm_df[sm_df["Sector"].astype(str) == str(sector)]
        for _, row in sel.iterrows():
            p = str(row["Param"]).strip()
            m = str(row["Material"]).strip()
            v = float(row["Value"])
            if p in sm_maps:
                sm_maps[p][m] = v

    def factory() -> AnchorClientAgent:
        return AnchorClientAgent(
            sector=sector,
            params=params,
            material_start_year_by_material=material_start_year_by_material,
            sm_initial_requirement_rate=sm_maps["initial_requirement_rate"],
            sm_initial_req_growth=sm_maps["initial_req_growth"],
            sm_ramp_requirement_rate=sm_maps["ramp_requirement_rate"],
            sm_ramp_req_growth=sm_maps["ramp_req_growth"],
            sm_steady_requirement_rate=sm_maps["steady_requirement_rate"],
            sm_steady_req_growth=sm_maps["steady_req_growth"],
        )

    return factory


def build_all_anchor_agent_factories(bundle: Phase1Bundle) -> Dict[str, Callable[[], AnchorClientAgent]]:
    """Return a registry mapping sector -> factory for all sectors in the inputs."""
    factories: Dict[str, Callable[[], AnchorClientAgent]] = {}
    for sector in bundle.lists.sectors:
        # Only include sectors that appear in anchor parameters and mapping
        if sector not in bundle.anchor.by_sector.columns:
            continue
        factories[sector] = build_anchor_agent_factory_for_sector(bundle, sector)
    if not factories:
        raise ValueError("No anchor agent factories were created; check inputs")
    return factories


__all__ = [
    "AnchorClientAgentState",
    "AnchorClientParams",
    "AnchorClientAgent",
    "build_anchor_agent_factory_for_sector",
    "build_all_anchor_agent_factories",
]


# -----------------------------
# Phase 17.3 — SM-mode ABM
# -----------------------------

@dataclass(frozen=True)
class AnchorClientSMParams:
    """Container for required per-(sector, material) parameters in SM-mode.

    All fields are numeric and come strictly from `anchor_params_sm` entries
    for the specific (sector, material) pair. Durations and delays are
    expressed in quarters; rates are expressed per quarter. The
    `anchor_start_year_years` is absolute time in years.
    """

    # Timing gates
    anchor_start_year_years: float
    anchor_client_activation_delay_quarters: float

    # Project lifecycle (per-quarter rates/durations)
    project_generation_rate: float
    max_projects_per_pc: float
    project_duration_quarters: float
    projects_to_client_conversion: float

    # Requirement phases (per-quarter base rate and per-quarter growth)
    initial_phase_duration_quarters: float
    ramp_phase_duration_quarters: float
    initial_requirement_rate: float
    initial_req_growth: float
    ramp_requirement_rate: float
    ramp_req_growth: float
    steady_requirement_rate: float
    steady_req_growth: float


class AnchorClientAgentSM:
    """Deterministic SM-mode agent bound to a single (sector, material).

    Lifecycle and requirement generation mirror `AnchorClientAgent` but the
    parameterization is strictly per-(sector, material) with no fallbacks.

    - States: POTENTIAL → PENDING_ACTIVATION → ACTIVE
    - Project generation uses accumulate-and-fire per step.
    - Activation occurs when completed projects ≥ threshold, after an
      activation delay (in quarters, converted to years).
    - Requirements are generated only when ACTIVE and `t_years` is past the
      material start year for this pair.
    """

    def __init__(
        self,
        *,
        sector: str,
        material: str,
        params: AnchorClientSMParams,
        agent_label: Optional[str] = None,
    ) -> None:
        self.sector: str = str(sector)
        self.material: str = str(material)
        self.params: AnchorClientSMParams = params
        self.label: str = agent_label or f"curious-puppy_{self.sector}_{self.material}"

        # Lifecycle state
        self.state: AnchorClientAgentState = AnchorClientAgentState.POTENTIAL
        self.activation_time_years: Optional[float] = None

        # Project accumulators
        self._project_start_accumulator: float = 0.0
        self._num_projects_started: int = 0
        self._project_completion_offsets_years: List[float] = []
        self._num_projects_completed: int = 0

        # Last-step requirement value for the bound material
        self.requirements: Dict[str, float] = {self.material: 0.0}

    # ----- Public properties -----
    @property
    def num_projects_started(self) -> int:
        return self._num_projects_started

    @property
    def num_projects_completed(self) -> int:
        return self._num_projects_completed

    # ----- Core behavior -----
    def act(self, t_years: float, round_no: int, step_no: int, *, dt_years: float = QUARTER_IN_YEARS) -> Dict[str, float]:
        """Advance the agent by one step and return requirements for this step.

        Parameters
        ----------
        t_years : float
            Current absolute simulation time in years
        dt_years : float
            Step size in years (default = 0.25 years = 1 quarter)
        """
        self._progress_projects_and_activation(t_years, dt_years)
        self.requirements = {self.material: self._generate_requirement_for_current_step(t_years)}
        return dict(self.requirements)

    # ----- Internal helpers -----
    def _progress_projects_and_activation(self, t_years: float, dt_years: float) -> None:
        if self.state is AnchorClientAgentState.POTENTIAL:
            # Complete existing projects first, then start new ones
            self._update_completed_projects(dt_years)
            self._maybe_start_projects(dt_years)

            # Threshold check for scheduling activation
            if (
                self.activation_time_years is None
                and self._num_projects_completed >= self.params.projects_to_client_conversion
            ):
                self.activation_time_years = t_years + _quarters_to_years(
                    self.params.anchor_client_activation_delay_quarters
                )
                self.state = AnchorClientAgentState.PENDING_ACTIVATION

        if self.state is AnchorClientAgentState.PENDING_ACTIVATION:
            if self.activation_time_years is not None and t_years >= self.activation_time_years:
                self.state = AnchorClientAgentState.ACTIVE

    def _maybe_start_projects(self, dt_years: float) -> None:
        max_projects = int(self.params.max_projects_per_pc)
        if self._num_projects_started >= max_projects:
            return
        scale = _steps_per_quarter(dt_years)
        self._project_start_accumulator += self.params.project_generation_rate * scale
        to_start = int(self._project_start_accumulator)
        if to_start <= 0:
            return
        can_start = min(to_start, max_projects - self._num_projects_started)
        if can_start <= 0:
            return
        completion_offset_years = _quarters_to_years(self.params.project_duration_quarters)
        for _ in range(can_start):
            self._num_projects_started += 1
            self._project_completion_offsets_years.append(completion_offset_years)
        self._project_start_accumulator -= to_start

    def _update_completed_projects(self, dt_years: float) -> None:
        if not self._project_completion_offsets_years:
            return
        decrement = float(dt_years)
        new_offsets: List[float] = []
        for remaining in self._project_completion_offsets_years:
            remaining_after = remaining - decrement
            if remaining_after <= 1e-12:
                self._num_projects_completed += 1
            else:
                new_offsets.append(remaining_after)
        self._project_completion_offsets_years = new_offsets

    def _generate_requirement_for_current_step(self, t_years: float) -> float:
        # Respect material start year gate and lifecycle state
        if t_years < self.params.anchor_start_year_years:
            return 0.0
        if self.state is not AnchorClientAgentState.ACTIVE:
            return 0.0

        assert self.activation_time_years is not None
        elapsed_years = max(0.0, t_years - self.activation_time_years)
        q_since_activation = max(0, int(elapsed_years / QUARTER_IN_YEARS + 1e-12))

        d_initial = max(0, int(round(self.params.initial_phase_duration_quarters)))
        d_ramp = max(0, int(round(self.params.ramp_phase_duration_quarters)))

        if q_since_activation < d_initial:
            return float(self.params.initial_requirement_rate * (1 + self.params.initial_req_growth) ** q_since_activation)

        if q_since_activation < d_initial + d_ramp:
            step_in_ramp = q_since_activation - d_initial
            return float(self.params.ramp_requirement_rate * (1 + self.params.ramp_req_growth) ** step_in_ramp)

        step_in_steady = q_since_activation - (d_initial + d_ramp)
        return float(self.params.steady_requirement_rate * (1 + self.params.steady_req_growth) ** step_in_steady)


def _require_anchor_sm(bundle: "Phase1Bundle", sector: str, material: str, param: str) -> float:
    """Strictly fetch per-(sector, material) parameter from `bundle.anchor_sm`.

    Missing triples raise with a precise message. Used exclusively by SM-mode
    factories to enforce 17.1 completeness guarantees at construction.
    """
    sm_df = getattr(bundle, "anchor_sm", None)
    if sm_df is None or sm_df.empty:
        raise ValueError("SM-mode requires anchor_params_sm; none loaded")
    sel = sm_df[
        (sm_df["Sector"].astype(str) == str(sector))
        & (sm_df["Material"].astype(str) == str(material))
        & (sm_df["Param"].astype(str) == str(param))
    ]
    if sel.empty:
        raise ValueError(f"Missing per-(sector, material) parameter ({sector}, {material}, {param}) for SM-mode")
    return float(sel.iloc[0]["Value"])


def build_sm_anchor_agent_factory(bundle: "Phase1Bundle", sector: str, material: str) -> Callable[[], AnchorClientAgentSM]:
    """Return a zero-arg factory that creates fresh SM-mode agents for (s,m).

    This factory pulls all parameters strictly from `bundle.anchor_sm` for the
    provided (sector, material) pair. No sector-level fallbacks are used.
    """
    # Build params strictly from SM table
    params = AnchorClientSMParams(
        anchor_start_year_years=float(_require_anchor_sm(bundle, sector, material, "anchor_start_year")),
        anchor_client_activation_delay_quarters=float(_require_anchor_sm(bundle, sector, material, "anchor_client_activation_delay")),
        project_generation_rate=float(_require_anchor_sm(bundle, sector, material, "project_generation_rate")),
        max_projects_per_pc=float(_require_anchor_sm(bundle, sector, material, "max_projects_per_pc")),
        project_duration_quarters=float(_require_anchor_sm(bundle, sector, material, "project_duration")),
        projects_to_client_conversion=float(_require_anchor_sm(bundle, sector, material, "projects_to_client_conversion")),
        initial_phase_duration_quarters=float(_require_anchor_sm(bundle, sector, material, "initial_phase_duration")),
        ramp_phase_duration_quarters=float(_require_anchor_sm(bundle, sector, material, "ramp_phase_duration")),
        initial_requirement_rate=float(_require_anchor_sm(bundle, sector, material, "initial_requirement_rate")),
        initial_req_growth=float(_require_anchor_sm(bundle, sector, material, "initial_req_growth")),
        ramp_requirement_rate=float(_require_anchor_sm(bundle, sector, material, "ramp_requirement_rate")),
        ramp_req_growth=float(_require_anchor_sm(bundle, sector, material, "ramp_req_growth")),
        steady_requirement_rate=float(_require_anchor_sm(bundle, sector, material, "steady_requirement_rate")),
        steady_req_growth=float(_require_anchor_sm(bundle, sector, material, "steady_req_growth")),
    )

    def factory() -> AnchorClientAgentSM:
        return AnchorClientAgentSM(sector=sector, material=material, params=params)

    return factory


# Export SM-mode symbols
__all__.extend([
    "AnchorClientSMParams",
    "AnchorClientAgentSM",
    "build_sm_anchor_agent_factory",
])


