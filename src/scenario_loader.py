from __future__ import annotations

"""
Phase 3 — Scenario Loader (YAML/JSON) & Strict Overrides

Responsibilities
- Load a single scenario file (YAML or JSON) containing optional `runspecs` and
  optional `overrides` blocks.
- Validate `runspecs` with defaults (2025.0→2032.0, dt=0.25) and basic
  consistency checks.
- Validate `overrides.constants` and `overrides.points` keys against the final
  element names implied by Phase 1 inputs and the naming conventions. Unknown
  keys are validation errors (strict policy).
- Coerce numeric values, sort lookup point arrays by time, and ensure all
  values are numeric.

Design notes
- We avoid coupling to the SD model. Instead, we compute the permissible set of
  override keys from Phase 1 inputs: anchor parameter names × sectors, other
  parameter names × materials, and lookup names per material.
- This module is pure and stateless; it accepts a Phase 1 bundle and a file
  path and returns a validated, normalized `Scenario` object.
"""

from dataclasses import dataclass
import difflib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import yaml

from .naming import (
    anchor_constant,
    anchor_constant_sm,
    max_capacity_lookup_name,
    other_constant,
    price_lookup_name,
)
from .phase1_data import Phase1Bundle
from .naming import price_converter as _price_conv_name, max_capacity_converter as _cap_conv_name


@dataclass(frozen=True)
class RunSpecs:
    starttime: float
    stoptime: float
    dt: float
    # Phase 17.1: global anchor mode switch
    # "sector" (default) = legacy behavior; sector-level creation and sector params allowed
    # "sm" = per-(sector, material) mode; requires complete anchor_params_sm and lists_sm
    anchor_mode: str = "sector"


@dataclass(frozen=True)
class Scenario:
    name: str
    runspecs: RunSpecs
    # Strictly validated and normalized
    constants: Dict[str, float]
    points: Dict[str, List[Tuple[float, float]]]
    # Phase 13: primary_map overrides (sector -> list[(material, start_year)])
    primary_map: Dict[str, List[Tuple[str, float]]] | None = None
    # Optional: SM universe supplied by scenario (Phase 17.x extension)
    # Represented as list of (Sector, Material) tuples; when provided, it takes precedence
    # over inputs.json lists_sm for this run.
    lists_sm: List[Tuple[str, str]] | None = None
    # Phase 14: seeds for pre-existing ACTIVE anchor clients at t0
    # Mapping of sector -> non-negative integer count
    seeds_active_anchor_clients: Dict[str, int] | None = None
    # Optional aging support (quarters) per sector; validated but not required
    seeds_elapsed_quarters: Dict[str, int] | None = None
    # Phase 14 (extension): seeds for direct clients (per material)
    seeds_direct_clients: Dict[str, int] | None = None
    # Phase 17.1: SM-mode seeds for anchor clients per (sector, material)
    # Mapping of sector -> material -> non-negative int
    seeds_active_anchor_clients_sm: Dict[str, Dict[str, int]] | None = None
    # SM-mode: optional aging per (sector, material) in quarters
    seeds_elapsed_quarters_sm: Dict[str, Dict[str, int]] | None = None
    # New: Seed completed projects backlog at t0 (Phase 17.x)
    # Sector-mode: mapping of sector -> total number of completed projects accrued pre-t0
    seeds_completed_projects: Dict[str, int] | None = None
    # SM-mode: mapping of sector -> material -> total completed projects pre-t0
    seeds_completed_projects_sm: Dict[str, Dict[str, int]] | None = None


DEFAULT_START = 2025.0
DEFAULT_STOP = 2032.0
DEFAULT_DT = 0.25


def _coerce_numeric(value: object, field_name: str) -> float:
    """Attempt to coerce an object to a primitive float, stripping simple symbols.

    Accepted inputs include numeric types and strings that may contain common
    currency or formatting symbols. This function does not apply semantic
    transformations (e.g., does not divide percents by 100); callers are
    responsible for interpreting units. This strictness avoids hidden defaults
    and keeps overrides explicit.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        # Remove common currency/formatting characters
        for ch in ["%", "$", "€", "£", ","]:
            s = s.replace(ch, "")
        try:
            return float(s)
        except ValueError as exc:  # re-raise with context
            raise ValueError(f"Non-numeric value for '{field_name}': {value!r}") from exc
    raise ValueError(f"Non-numeric value for '{field_name}': {value!r}")


def _coerce_points(
    points: Sequence[Sequence[object]], lookup_name: str
) -> List[Tuple[float, float]]:
    """Validate and normalize a list of [time, value] pairs to sorted floats.

    The function is deliberately strict about structure and monotonicity to
    prevent subtle runtime errors in lookups that expect a well-behaved time
    axis in BPTK_Py. We sort by time and require strictly increasing times.
    """
    normalized: List[Tuple[float, float]] = []
    for idx, pair in enumerate(points):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(
                f"Points for '{lookup_name}' must be a list of [time, value] pairs; bad entry at index {idx}: {pair!r}"
            )
        t = _coerce_numeric(pair[0], f"{lookup_name}[{idx}].time")
        v = _coerce_numeric(pair[1], f"{lookup_name}[{idx}].value")
        normalized.append((t, v))

    # Sort by time and validate strictly increasing times
    normalized.sort(key=lambda x: x[0])
    for i in range(1, len(normalized)):
        if normalized[i][0] <= normalized[i - 1][0]:
            raise ValueError(
                f"Points for '{lookup_name}' must have strictly increasing time values; offending sequence: {normalized}"
            )
    return normalized


def _nearest_matches(name: str, candidates: Iterable[str], n: int = 3) -> List[str]:
    return difflib.get_close_matches(name, list(candidates), n=n)


def _collect_permissible_override_keys(bundle: Phase1Bundle, *, anchor_mode: str = "sector", extra_sm_pairs: Optional[List[Tuple[str, str]]] = None) -> Tuple[set, set]:
    """Return (constants_keys, points_keys) permissible for overrides.

    - constants_keys include anchor param × sector and other param × material
    - points_keys include price_<material> and max_capacity_<material>
    """
    # Build the complete set of constants and lookup names that a scenario is
    # allowed to override, based exclusively on the Phase 1 inputs. This keeps
    # Phase 3 validation independent of the SD model build order.
    constants: set = set()
    # Sector-mode: anchor params per sector allowed; SM-mode: only per-(s,m) anchor params allowed
    # Phase 17.5: enforce SM-only constants surface for anchor params when anchor_mode == "sm".
    if anchor_mode != "sm":
        for param in bundle.anchor.by_sector.index.astype(str):
            for sector in bundle.anchor.by_sector.columns.astype(str):
                constants.add(anchor_constant(param, sector))
    # Other parameters: DataFrame index; columns are material names
    for param in bundle.other.by_material.index.astype(str):
        for material in bundle.other.by_material.columns.astype(str):
            constants.add(other_constant(param, material))

    # Per-(sector, material) anchor params (Phase 16/17):
    # - In sector-mode: allow targeted params to be overridden per (s,m)
    # - In SM-mode: allow the FULL anchor set per (s,m) listed in Phase 17.1
    if anchor_mode == "sm":
        sm_params = {
            "anchor_start_year",
            "anchor_client_activation_delay",
            "anchor_lead_generation_rate",
            "lead_to_pc_conversion_rate",
            "project_generation_rate",
            "max_projects_per_pc",
            "project_duration",
            "projects_to_client_conversion",
            "initial_phase_duration",
            "ramp_phase_duration",
            "ATAM",
            "initial_requirement_rate",
            "initial_req_growth",
            "ramp_requirement_rate",
            "ramp_req_growth",
            "steady_requirement_rate",
            "steady_req_growth",
            "requirement_to_order_lag",
        }
    else:
        sm_params = {
            "requirement_to_order_lag",
            "initial_requirement_rate",
            "initial_req_growth",
            "ramp_requirement_rate",
            "ramp_req_growth",
            "steady_requirement_rate",
            "steady_req_growth",
        }
    # SM universe from lists_sm if available, else derive from primary_map; include extra pairs from scenario overrides
    import pandas as pd
    sm_df_universe = getattr(bundle, "lists_sm", None)
    if sm_df_universe is None or sm_df_universe.empty:
        sm_df_universe = bundle.primary_map.long[["Sector", "Material"]].drop_duplicates()
    if extra_sm_pairs:
        extra_df = pd.DataFrame(extra_sm_pairs, columns=["Sector", "Material"]).drop_duplicates()
        sm_df_universe = pd.concat([sm_df_universe, extra_df], ignore_index=True).drop_duplicates()
    for _, sm in sm_df_universe.iterrows():
        s = str(sm.get("Sector")).strip()
        m = str(sm.get("Material")).strip()
        for p in sm_params:
            constants.add(anchor_constant_sm(p, s, m))

    # Lookups for price and capacity are per material
    points: set = set()
    for material in bundle.lists.materials:
        points.add(price_lookup_name(material))
        points.add(max_capacity_lookup_name(material))
    return constants, points


def _sm_constants_from_overrides(constants: Mapping[str, float], bundle: Phase1Bundle, params: set[str]) -> set[Tuple[str, str, str]]:
    """Return set of (Sector, Material, Param) triples that are present in scenario overrides.

    This helps SM-mode consider scenario-provided constants as satisfying coverage, even if
    `inputs.json` lacks those triples.
    """
    # Build SM universe from explicit lists_sm if present; else derive from primary_map
    sm_df_universe = getattr(bundle, "lists_sm", None)
    if sm_df_universe is None or sm_df_universe.empty:
        sm_df_universe = bundle.primary_map.long[["Sector", "Material"]].drop_duplicates()
    found: set[Tuple[str, str, str]] = set()
    for _, sm in sm_df_universe.iterrows():
        s = str(sm["Sector"]).strip()
        m = str(sm["Material"]).strip()
        for p in params:
            name = anchor_constant_sm(p, s, m)
            if name in constants:
                found.add((s, m, p))
    return found


def _validate_seeds(raw_seeds: Optional[Mapping[str, object]], *, bundle: Phase1Bundle) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Validate and normalize Phase 14 seeding configuration.

    Schema (YAML):
      seeds:
        active_anchor_clients: { <sector>: <int>, ... }
        elapsed_quarters: { <sector>: <int>, ... }   # optional; validated if present

    Rules:
    - Sectors must exist in bundle.lists.sectors
    - Values must be integers >= 0
    - Unknown keys under seeds raise an error
    """
    if raw_seeds is None:
        return {}, {}
    if not isinstance(raw_seeds, Mapping):
        raise ValueError("'seeds' must be a mapping with 'active_anchor_clients' and optional 'elapsed_quarters'")

    sectors_set = set(map(str, bundle.lists.sectors))

    def _normalize_counts(block: Optional[Mapping[str, object]], block_name: str) -> Dict[str, int]:
        if block is None:
            return {}
        if not isinstance(block, Mapping):
            raise ValueError(f"'seeds.{block_name}' must be a mapping of sector -> non-negative integer")
        out: Dict[str, int] = {}
        for sector, raw_val in block.items():
            s = str(sector)
            if s not in sectors_set:
                raise ValueError(f"seeds.{block_name} contains unknown sector '{s}'")
            # Accept ints, numeric strings; coerce via _coerce_numeric then check integer-ness
            v_float = _coerce_numeric(raw_val, f"seeds.{block_name}['{s}']")
            if v_float < 0 or int(v_float) != v_float:
                raise ValueError(f"seeds.{block_name}['{s}'] must be a non-negative integer")
            out[s] = int(v_float)
        return out

    active_map = _normalize_counts(raw_seeds.get("active_anchor_clients"), "active_anchor_clients")
    elapsed_map = _normalize_counts(raw_seeds.get("elapsed_quarters"), "elapsed_quarters")

    # Guard against extra/unknown keys at this level
    allowed = {"active_anchor_clients", "elapsed_quarters", "direct_clients", "active_anchor_clients_sm", "completed_projects", "completed_projects_sm", "elapsed_quarters_sm", "__scenario_lists_sm__"}
    extras = set(raw_seeds.keys()) - allowed
    if extras:
        raise ValueError(f"seeds contains unknown keys: {', '.join(sorted(extras))}")
    return active_map, elapsed_map


def _validate_seeds_sm(raw_seeds: Optional[Mapping[str, object]], *, bundle: Phase1Bundle, anchor_mode: str) -> Dict[str, Dict[str, int]]:
    """Phase 17.1: Validate SM-mode seeding configuration.

    Schema (YAML):
      seeds:
        active_anchor_clients_sm: { <Sector>: { <Material>: <int> } }
    Only valid when anchor_mode = "sm". Requires lists_sm non-empty and explicit.
    """
    if anchor_mode != "sm":
        return {}
    if raw_seeds is None or not isinstance(raw_seeds, Mapping):
        return {}
    block = raw_seeds.get("active_anchor_clients_sm")
    if block is None:
        return {}
    if not isinstance(block, Mapping):
        raise ValueError("seeds.active_anchor_clients_sm must be a mapping of sector -> mapping(material -> int)")

    # Build SM universe. Allow scenario-level lists_sm to satisfy this requirement when present.
    # The scenario-level lists_sm is parsed earlier in load_and_validate_scenario and stored temporarily
    # on a private key in the seeds block for validation purposes.
    import pandas as pd
    scenario_sm_pairs: List[Tuple[str, str]] | None = None
    if isinstance(raw_seeds, Mapping):
        scenario_sm_pairs = raw_seeds.get("__scenario_lists_sm__")  # type: ignore[assignment]
    sm_df = None
    if scenario_sm_pairs:
        sm_df = pd.DataFrame(scenario_sm_pairs, columns=["Sector", "Material"]).drop_duplicates()
    else:
        sm_df = getattr(bundle, "lists_sm", None)
        if sm_df is None or sm_df.empty:
            raise ValueError("SM-mode requires non-empty lists_sm (provide via scenario.lists_sm or inputs.json)")
        # If coming from inputs.json, enforce explicitness to avoid derived lists
        if not getattr(bundle, "lists_sm_explicit", False):
            raise ValueError("SM-mode requires lists_sm be explicitly provided (scenario or inputs.json), not derived")

    # Allowed pairs set
    allowed_pairs = {(str(r["Sector"]), str(r["Material"])) for _, r in sm_df.iterrows()}

    out: Dict[str, Dict[str, int]] = {}
    for sector, mat_map in block.items():
        s = str(sector)
        if not isinstance(mat_map, Mapping):
            raise ValueError(f"seeds.active_anchor_clients_sm['{s}'] must be a mapping of material -> non-negative integer")
        for material, raw_val in mat_map.items():
            m = str(material)
            if (s, m) not in allowed_pairs:
                raise ValueError(f"seeds.active_anchor_clients_sm contains unknown pair ('{s}', '{m}') not in lists_sm")
            v_float = _coerce_numeric(raw_val, f"seeds.active_anchor_clients_sm['{s}']['{m}']")
            if v_float < 0 or int(v_float) != v_float:
                raise ValueError(f"seeds.active_anchor_clients_sm['{s}']['{m}'] must be a non-negative integer")
            out.setdefault(s, {})[m] = int(v_float)
    return out


def _validate_completed_projects(raw_seeds: Optional[Mapping[str, object]], *, bundle: Phase1Bundle, anchor_mode: str) -> Dict[str, int]:
    """Validate sector-mode completed projects backlog seeds.

    Schema:
      seeds:
        completed_projects: { <sector>: <int> }

    Only valid when anchor_mode != "sm" (sector-mode). Values must be non-negative integers and sectors valid.
    """
    if raw_seeds is None or not isinstance(raw_seeds, Mapping):
        return {}
    if anchor_mode == "sm":
        # Sector-level completed projects not applicable in SM-mode
        if "completed_projects" in raw_seeds:
            raise ValueError("SM-mode prohibits seeds.completed_projects; use seeds.completed_projects_sm instead")
        return {}
    block = raw_seeds.get("completed_projects")
    if block is None:
        return {}
    if not isinstance(block, Mapping):
        raise ValueError("seeds.completed_projects must be a mapping of sector -> non-negative integer")
    sectors_set = set(map(str, bundle.lists.sectors))
    out: Dict[str, int] = {}
    for sector, raw_val in block.items():
        s = str(sector)
        if s not in sectors_set:
            raise ValueError(f"seeds.completed_projects contains unknown sector '{s}'")
        v_float = _coerce_numeric(raw_val, f"seeds.completed_projects['{s}']")
        if v_float < 0 or int(v_float) != v_float:
            raise ValueError(f"seeds.completed_projects['{s}'] must be a non-negative integer")
        out[s] = int(v_float)
    return out


def _validate_completed_projects_sm(raw_seeds: Optional[Mapping[str, object]], *, bundle: Phase1Bundle, anchor_mode: str) -> Dict[str, Dict[str, int]]:
    """Validate SM-mode completed projects backlog per (sector, material).

    Schema:
      seeds:
        completed_projects_sm: { <Sector>: { <Material>: <int> } }
    Only valid when anchor_mode == "sm" and pairs must exist in lists_sm universe.
    """
    if anchor_mode != "sm":
        return {}
    if raw_seeds is None or not isinstance(raw_seeds, Mapping):
        return {}
    block = raw_seeds.get("completed_projects_sm")
    if block is None:
        return {}
    if not isinstance(block, Mapping):
        raise ValueError("seeds.completed_projects_sm must be a mapping of sector -> mapping(material -> int)")
    # Use scenario-provided lists_sm if available (injected earlier on private key), else bundle.lists_sm
    import pandas as pd
    scenario_sm_pairs: List[Tuple[str, str]] | None = None
    if isinstance(raw_seeds, Mapping):
        scenario_sm_pairs = raw_seeds.get("__scenario_lists_sm__")  # type: ignore[assignment]
    if scenario_sm_pairs:
        sm_df = pd.DataFrame(scenario_sm_pairs, columns=["Sector", "Material"]).drop_duplicates()
    else:
        sm_df = getattr(bundle, "lists_sm", None)
        if sm_df is None or sm_df.empty:
            raise ValueError("SM-mode requires non-empty lists_sm (provide via scenario or inputs.json)")
        if not getattr(bundle, "lists_sm_explicit", False):
            raise ValueError("SM-mode requires lists_sm be explicitly provided (scenario or inputs.json), not derived")
    allowed_pairs = {(str(r["Sector"]), str(r["Material"])) for _, r in sm_df.iterrows()}
    out: Dict[str, Dict[str, int]] = {}
    for sector, mat_map in block.items():
        s = str(sector)
        if not isinstance(mat_map, Mapping):
            raise ValueError(f"seeds.completed_projects_sm['{s}'] must be a mapping of material -> non-negative integer")
        for material, raw_val in mat_map.items():
            m = str(material)
            if (s, m) not in allowed_pairs:
                raise ValueError(f"seeds.completed_projects_sm contains unknown pair ('{s}', '{m}') not in lists_sm")
            v_float = _coerce_numeric(raw_val, f"seeds.completed_projects_sm['{s}']['{m}']")
            if v_float < 0 or int(v_float) != v_float:
                raise ValueError(f"seeds.completed_projects_sm['{s}']['{m}'] must be a non-negative integer")
            out.setdefault(s, {})[m] = int(v_float)
    return out


def _validate_elapsed_quarters_sm(raw_seeds: Optional[Mapping[str, object]], *, bundle: Phase1Bundle, anchor_mode: str) -> Dict[str, Dict[str, int]]:
    """Validate SM-mode elapsed quarters per (sector, material).

    Schema:
      seeds:
        elapsed_quarters_sm: { <Sector>: { <Material>: <int> } }
    Only valid when anchor_mode == "sm".
    """
    if anchor_mode != "sm":
        return {}
    if raw_seeds is None or not isinstance(raw_seeds, Mapping):
        return {}
    block = raw_seeds.get("elapsed_quarters_sm")
    if block is None:
        return {}
    if not isinstance(block, Mapping):
        raise ValueError("seeds.elapsed_quarters_sm must be a mapping of sector -> mapping(material -> int)")
    # Build SM universe
    import pandas as pd
    sm_df = getattr(bundle, "lists_sm", None)
    if sm_df is None or sm_df.empty:
        # Allow scenario-level lists_sm injected earlier for validation when present
        scenario_sm_pairs: List[Tuple[str, str]] | None = raw_seeds.get("__scenario_lists_sm__")  # type: ignore[assignment]
        if scenario_sm_pairs:
            sm_df = pd.DataFrame(scenario_sm_pairs, columns=["Sector", "Material"]).drop_duplicates()
        else:
            raise ValueError("SM-mode requires non-empty lists_sm (provide via scenario or inputs.json) to validate elapsed_quarters_sm")
    allowed_pairs = {(str(r["Sector"]), str(r["Material"])) for _, r in sm_df.iterrows()}
    out: Dict[str, Dict[str, int]] = {}
    for sector, mat_map in block.items():
        s = str(sector)
        if not isinstance(mat_map, Mapping):
            raise ValueError(f"seeds.elapsed_quarters_sm['{s}'] must be a mapping of material -> non-negative integer")
        for material, raw_val in mat_map.items():
            m = str(material)
            if (s, m) not in allowed_pairs:
                raise ValueError(f"seeds.elapsed_quarters_sm contains unknown pair ('{s}', '{m}') not in lists_sm")
            v_float = _coerce_numeric(raw_val, f"seeds.elapsed_quarters_sm['{s}']['{m}']")
            if v_float < 0 or int(v_float) != v_float:
                raise ValueError(f"seeds.elapsed_quarters_sm['{s}']['{m}'] must be a non-negative integer")
            out.setdefault(s, {})[m] = int(v_float)
    return out


def _validate_direct_seeds(raw_seeds: Optional[Mapping[str, object]], *, bundle: Phase1Bundle) -> Dict[str, int]:
    """Validate and normalize seeding for direct clients per material.

    Schema:
      seeds:
        direct_clients: { <material>: <int>, ... }
    """
    if raw_seeds is None:
        return {}
    if not isinstance(raw_seeds, Mapping):
        return {}
    dc = raw_seeds.get("direct_clients")
    if dc is None:
        return {}
    if not isinstance(dc, Mapping):
        raise ValueError("'seeds.direct_clients' must be a mapping of material -> non-negative integer")
    mats_set = set(map(str, bundle.lists.materials))
    out: Dict[str, int] = {}
    for material, raw_val in dc.items():
        m = str(material)
        if m not in mats_set:
            raise ValueError(f"seeds.direct_clients contains unknown material '{m}'")
        v_float = _coerce_numeric(raw_val, f"seeds.direct_clients['{m}']")
        if v_float < 0 or int(v_float) != v_float:
            raise ValueError(f"seeds.direct_clients['{m}'] must be a non-negative integer")
        out[m] = int(v_float)
    return out


def _validate_primary_map_override(
    raw_pm: object, *, bundle: Phase1Bundle
) -> Dict[str, List[Tuple[str, float]]]:
    """Validate and normalize primary_map overrides.

    Schema:
      overrides.primary_map:
        <sector>: [ { material: <str>, start_year: <float> }, ... ]

    Rules:
    - Sector must exist in `bundle.lists.sectors`
    - Material must exist in `bundle.lists.materials`
    - start_year must be numeric
    - Material must also appear in other tables (other params, production, pricing)
    - Deduplicate (sector, material); last occurrence wins
    """
    if raw_pm is None:
        return {}
    if not isinstance(raw_pm, dict):
        raise ValueError("overrides.primary_map must be a mapping of sector -> list[ {material, start_year} ]")

    sectors_set = set(bundle.lists.sectors)
    mats_set = set(bundle.lists.materials)
    other_cols = set(bundle.other.by_material.columns.astype(str))
    prod_mats = set(bundle.production.long["Material"].unique())
    price_mats = set(bundle.pricing.long["Material"].unique())

    out: Dict[str, List[Tuple[str, float]]] = {}
    for sector, entries in raw_pm.items():
        if sector not in sectors_set:
            raise ValueError(f"overrides.primary_map has unknown sector '{sector}'")
        if not isinstance(entries, (list, tuple)):
            raise ValueError(f"overrides.primary_map['{sector}'] must be a list of entries")
        normalized: Dict[str, float] = {}
        for idx, e in enumerate(entries):
            if not isinstance(e, dict):
                raise ValueError(
                    f"overrides.primary_map['{sector}'][{idx}] must be a mapping with 'material' and 'start_year'"
                )
            mat = str(e.get("material", "")).strip()
            if not mat:
                raise ValueError(f"overrides.primary_map['{sector}'][{idx}] missing 'material'")
            if mat not in mats_set:
                raise ValueError(
                    f"overrides.primary_map['{sector}'][{idx}] material '{mat}' is not in inputs lists.materials"
                )
            try:
                sy = _coerce_numeric(e.get("start_year"), f"overrides.primary_map['{sector}'][{idx}].start_year")
            except Exception as exc:
                raise
            # Cross-table presence checks
            if mat not in other_cols:
                raise ValueError(
                    f"overrides.primary_map['{sector}'][{idx}] material '{mat}' not present in other_params"
                )
            if mat not in prod_mats:
                raise ValueError(
                    f"overrides.primary_map['{sector}'][{idx}] material '{mat}' not present in production table"
                )
            if mat not in price_mats:
                raise ValueError(
                    f"overrides.primary_map['{sector}'][{idx}] material '{mat}' not present in pricing table"
                )
            normalized[mat] = float(sy)
        if normalized:
            out[sector] = [(m, normalized[m]) for m in sorted(normalized.keys())]
    return out


def _validate_overrides(
    overrides: Mapping[str, object],
    permissible_constants: set,
    permissible_points: set,
) -> Tuple[Dict[str, float], Dict[str, List[Tuple[float, float]]]]:
    """Validate overrides blocks and return normalized (constants, points)."""
    constants_block = overrides.get("constants", {}) if overrides else {}
    points_block = overrides.get("points", {}) if overrides else {}

    if not isinstance(constants_block, Mapping):
        raise ValueError("overrides.constants must be a mapping of name -> value")
    if not isinstance(points_block, Mapping):
        raise ValueError("overrides.points must be a mapping of lookup_name -> [[t,v], ...]")

    constants_out: Dict[str, float] = {}
    points_out: Dict[str, List[Tuple[float, float]]] = {}

    # Validate constants
    unknown_constants: List[str] = []
    for name, raw_value in constants_block.items():
        if name not in permissible_constants:
            unknown_constants.append(name)
            continue
        constants_out[name] = _coerce_numeric(raw_value, f"constants['{name}']")

    # Validate points
    unknown_points: List[str] = []
    for name, raw_points in points_block.items():
        if name not in permissible_points:
            unknown_points.append(name)
            continue
        if not isinstance(raw_points, Sequence):
            raise ValueError(
                f"overrides.points['{name}'] must be a list of [time, value] pairs"
            )
        points_out[name] = _coerce_points(raw_points, name)

    if unknown_constants or unknown_points:
        messages: List[str] = []
        if unknown_constants:
            messages.append(
                "Unknown constants: "
                + ", ".join(
                    f"{n} (suggest: {', '.join(_nearest_matches(n, permissible_constants))})"
                    for n in unknown_constants
                )
            )
        if unknown_points:
            messages.append(
                "Unknown points: "
                + ", ".join(
                    f"{n} (suggest: {', '.join(_nearest_matches(n, permissible_points))})"
                    for n in unknown_points
                )
            )
        raise ValueError(
            "Scenario overrides contain unknown keys. " + " | ".join(messages)
        )

    return constants_out, points_out


def _load_raw_scenario(path: Path) -> Dict[str, object]:
    """Load YAML/JSON as a plain dict; ensure the root is a mapping."""
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        # Default to YAML if no/unknown extension
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Scenario file must deserialize to a mapping/dictionary at top level")
    return data


def _validate_runspecs(raw_runspecs: Optional[Mapping[str, object]]) -> RunSpecs:
    # Apply defaults per architecture when fields are not provided
    rs = raw_runspecs or {}
    start = _coerce_numeric(rs.get("starttime", DEFAULT_START), "runspecs.starttime")
    stop = _coerce_numeric(rs.get("stoptime", DEFAULT_STOP), "runspecs.stoptime")
    dt = _coerce_numeric(rs.get("dt", DEFAULT_DT), "runspecs.dt")

    if dt <= 0:
        raise ValueError("runspecs.dt must be positive")
    if start >= stop:
        raise ValueError("runspecs.starttime must be less than runspecs.stoptime")
    # Phase 17.1: anchor_mode
    mode = str(rs.get("anchor_mode", "sector")).strip().lower()
    if mode not in {"sector", "sm"}:
        raise ValueError("runspecs.anchor_mode must be either 'sector' or 'sm'")
    return RunSpecs(start, stop, dt, mode)


def load_and_validate_scenario(
    path: Path, *, bundle: Phase1Bundle
) -> Scenario:
    """Load a scenario file and validate it against Phase 1 inputs.

    Parameters
    ----------
    path : Path
        Path to YAML or JSON scenario file
    bundle : Phase1Bundle
        Phase 1 inputs containing sectors, materials, and parameter names

    Returns
    -------
    Scenario
        Validated, normalized scenario data structure
    """
    # 1) Deserialize
    raw = _load_raw_scenario(path)

    # 2) Normalize name and runspecs with defaults
    name = str(raw.get("name") or path.stem)
    runspecs = _validate_runspecs(raw.get("runspecs"))

    # 3) Phase 13: optional primary_map overrides (validate early to expand permissible keys)
    pm_overrides = {}
    overrides_block = raw.get("overrides", {}) or {}
    if "primary_map" in overrides_block:
        pm_overrides = _validate_primary_map_override(overrides_block.get("primary_map"), bundle=bundle)

    # Build extra (sector, material) pairs from primary_map overrides to expand permissible constants surface
    extra_pairs: List[Tuple[str, str]] = []
    for sector, entries in (pm_overrides or {}).items():
        for (mat, _sy) in entries:
            extra_pairs.append((sector, mat))

    # 3a) Optional scenario-level lists_sm (SM universe). Validate against lists and store as tuples.
    scenario_lists_sm_pairs: List[Tuple[str, str]] = []
    raw_lists_sm = raw.get("lists_sm")
    if raw_lists_sm is not None:
        if not isinstance(raw_lists_sm, (list, tuple)):
            raise ValueError("lists_sm must be a list of mappings with keys 'Sector' and 'Material'")
        sectors_set = set(map(str, bundle.lists.sectors))
        mats_set = set(map(str, bundle.lists.materials))
        seen: set[Tuple[str, str]] = set()
        for idx, entry in enumerate(raw_lists_sm):
            if not isinstance(entry, Mapping):
                raise ValueError(f"lists_sm[{idx}] must be a mapping with 'Sector' and 'Material'")
            s = str(entry.get("Sector", "")).strip()
            m = str(entry.get("Material", "")).strip()
            if not s or not m:
                raise ValueError(f"lists_sm[{idx}] missing Sector or Material")
            if s not in sectors_set:
                raise ValueError(f"lists_sm[{idx}] references unknown sector '{s}'")
            if m not in mats_set:
                raise ValueError(f"lists_sm[{idx}] references unknown material '{m}'")
            pair = (s, m)
            if pair not in seen:
                seen.add(pair)
                scenario_lists_sm_pairs.append(pair)
        # Expand permissible keys surface using scenario-provided SM universe
        extra_pairs.extend(scenario_lists_sm_pairs)

    # 4) Build the whitelist of valid override keys from Phase 1 inputs + scenario primary_map pairs
    permissible_constants, permissible_points = _collect_permissible_override_keys(
        bundle, anchor_mode=runspecs.anchor_mode, extra_sm_pairs=extra_pairs or None
    )
    constants, points = _validate_overrides(
        raw.get("overrides", {}) or {}, permissible_constants, permissible_points
    )

    # Phase 14: seeds (scenario-specific)
    seeds_block = raw.get("seeds")
    # Inject scenario-level lists_sm pairs for seeds validation (private key, stripped later)
    if isinstance(seeds_block, dict) and scenario_lists_sm_pairs:
        # Make a shallow copy to avoid mutating user's dict
        seeds_block = dict(seeds_block)
        seeds_block["__scenario_lists_sm__"] = scenario_lists_sm_pairs  # type: ignore[index]
    seeds_active, seeds_elapsed = _validate_seeds(seeds_block, bundle=bundle)
    seeds_direct = _validate_direct_seeds(seeds_block, bundle=bundle)
    seeds_sm = _validate_seeds_sm(seeds_block, bundle=bundle, anchor_mode=runspecs.anchor_mode)
    seeds_completed = _validate_completed_projects(seeds_block, bundle=bundle, anchor_mode=runspecs.anchor_mode)
    seeds_completed_sm = _validate_completed_projects_sm(seeds_block, bundle=bundle, anchor_mode=runspecs.anchor_mode)
    seeds_elapsed_sm = _validate_elapsed_quarters_sm(seeds_block, bundle=bundle, anchor_mode=runspecs.anchor_mode)

    # Phase 17.1/17.5: When in SM-mode, enforce strict rules
    if runspecs.anchor_mode == "sm":
        # Prohibit sector-level seeding in SM-mode (checked before other SM validations to surface the right error)
        if seeds_active:
            raise ValueError("SM-mode prohibits seeds.active_anchor_clients; use seeds.active_anchor_clients_sm instead")
        # Validate lists_sm exists (scenario-level satisfies requirement); prefer scenario-provided pairs
        import pandas as pd
        if scenario_lists_sm_pairs:
            sm_df = pd.DataFrame(scenario_lists_sm_pairs, columns=["Sector", "Material"]).drop_duplicates()
        else:
            sm_df = getattr(bundle, "lists_sm", None)
            if sm_df is None or sm_df.empty:
                raise ValueError("SM-mode requires non-empty lists_sm (provide via scenario or inputs.json)")
            if not getattr(bundle, "lists_sm_explicit", False):
                raise ValueError("SM-mode requires lists_sm be explicitly provided (scenario or inputs.json), not derived")
        # Build coverage matrix for targeted params
        targeted_sm_params = {
            "anchor_start_year",
            "anchor_client_activation_delay",
            "anchor_lead_generation_rate",
            "lead_to_pc_conversion_rate",
            "project_generation_rate",
            "max_projects_per_pc",
            "project_duration",
            "projects_to_client_conversion",
            "initial_phase_duration",
            "ramp_phase_duration",
            "ATAM",
            "initial_requirement_rate",
            "initial_req_growth",
            "ramp_requirement_rate",
            "ramp_req_growth",
            "steady_requirement_rate",
            "steady_req_growth",
            "requirement_to_order_lag",
        }
        anchor_sm_df = getattr(bundle, "anchor_sm", None)
        if anchor_sm_df is None or anchor_sm_df.empty:
            raise ValueError("SM-mode requires anchor_params_sm with full coverage for all targeted parameters and pairs in lists_sm")
        # Create a set of available triples
        available = {
            (str(r["Sector"]).strip(), str(r["Material"]).strip(), str(r["Param"]).strip())
            for _, r in anchor_sm_df.iterrows()
        }
        # Also count scenario-provided per-(s,m) constants toward coverage
        available |= _sm_constants_from_overrides(constants, bundle, targeted_sm_params)
        missing: list[str] = []
        for _, row in sm_df.iterrows():
            s = str(row["Sector"]).strip()
            m = str(row["Material"]).strip()
            for p in targeted_sm_params:
                if (s, m, p) not in available:
                    missing.append(f"({s}, {m}, {p})")
        if missing:
            # Keep message concise but actionable; cap long lists
            preview = ", ".join(missing[:10]) + (" ..." if len(missing) > 10 else "")
            raise ValueError(
                "SM-mode missing per-(sector, material) parameters for: " + preview
            )

    return Scenario(
        name=name,
        runspecs=runspecs,
        constants=constants,
        points=points,
        primary_map=pm_overrides or None,
        lists_sm=scenario_lists_sm_pairs or None,
        seeds_active_anchor_clients=seeds_active or None,
        seeds_elapsed_quarters=seeds_elapsed or None,
        seeds_direct_clients=seeds_direct or None,
        seeds_active_anchor_clients_sm=seeds_sm or None,
        seeds_elapsed_quarters_sm=seeds_elapsed_sm or None,
        seeds_completed_projects=seeds_completed or None,
        seeds_completed_projects_sm=seeds_completed_sm or None,
    )


def list_permissible_override_keys(
    bundle: Phase1Bundle,
    *,
    anchor_mode: str = "sector",
    extra_sm_pairs: Optional[List[Tuple[str, str]]] = None,
) -> dict:
    """Return permissible override keys for constants and points.

    This is a thin, stable wrapper around the internal whitelist builder so the UI
    can query valid element names without importing private helpers.

    Returns a dictionary:
      { "constants": set[str], "points": set[str] }
    """
    constants, points = _collect_permissible_override_keys(
        bundle, anchor_mode=anchor_mode, extra_sm_pairs=extra_sm_pairs
    )
    return {"constants": constants, "points": points}


def validate_scenario_dict(bundle: Phase1Bundle, scenario_dict: Mapping[str, object]):
    """Validate an in-memory scenario dictionary and return a `Scenario` object.

    The logic mirrors `load_and_validate_scenario`, but accepts a pre-constructed
    dictionary instead of loading from disk. Raises ValueError with actionable
    messages on validation failures.
    """
    if not isinstance(scenario_dict, Mapping):
        raise ValueError("scenario_dict must be a mapping/dict at the root")

    # Name and runspecs
    name = str(scenario_dict.get("name") or "untitled")
    runspecs = _validate_runspecs(scenario_dict.get("runspecs"))

    # Primary map overrides (optional) — validate early to expand permissible keys
    pm_overrides = {}
    overrides_block = scenario_dict.get("overrides", {}) or {}
    if isinstance(overrides_block, Mapping) and "primary_map" in overrides_block:
        pm_overrides = _validate_primary_map_override(overrides_block.get("primary_map"), bundle=bundle)

    # Extra (sector, material) pairs from primary_map to expand constants surface
    extra_pairs: List[Tuple[str, str]] = []
    for sector, entries in (pm_overrides or {}).items():
        for (mat, _sy) in entries:
            extra_pairs.append((sector, mat))

    # Optional scenario-level lists_sm
    scenario_lists_sm_pairs: List[Tuple[str, str]] = []
    raw_lists_sm = scenario_dict.get("lists_sm")
    if raw_lists_sm is not None:
        if not isinstance(raw_lists_sm, (list, tuple)):
            raise ValueError("lists_sm must be a list of mappings with keys 'Sector' and 'Material'")
        sectors_set = set(map(str, bundle.lists.sectors))
        mats_set = set(map(str, bundle.lists.materials))
        seen: set[Tuple[str, str]] = set()
        for idx, entry in enumerate(raw_lists_sm):
            if not isinstance(entry, Mapping):
                raise ValueError(f"lists_sm[{idx}] must be a mapping with 'Sector' and 'Material'")
            s = str(entry.get("Sector", "")).strip()
            m = str(entry.get("Material", "")).strip()
            if not s or not m:
                raise ValueError(f"lists_sm[{idx}] missing Sector or Material")
            if s not in sectors_set:
                raise ValueError(f"lists_sm[{idx}] references unknown sector '{s}'")
            if m not in mats_set:
                raise ValueError(f"lists_sm[{idx}] references unknown material '{m}'")
            pair = (s, m)
            if pair not in seen:
                seen.add(pair)
                scenario_lists_sm_pairs.append(pair)
        extra_pairs.extend(scenario_lists_sm_pairs)

    # Permissible keys then overrides normalization
    permissible_constants, permissible_points = _collect_permissible_override_keys(
        bundle, anchor_mode=runspecs.anchor_mode, extra_sm_pairs=extra_pairs or None
    )
    constants, points = _validate_overrides(
        overrides_block, permissible_constants, permissible_points
    )

    # Seeds (Phase 14 and SM-mode Phase 17.1)
    seeds_block = scenario_dict.get("seeds")
    if isinstance(seeds_block, dict) and scenario_lists_sm_pairs:
        seeds_block = dict(seeds_block)
        seeds_block["__scenario_lists_sm__"] = scenario_lists_sm_pairs  # type: ignore[index]
    seeds_active, seeds_elapsed = _validate_seeds(seeds_block, bundle=bundle)
    seeds_direct = _validate_direct_seeds(seeds_block, bundle=bundle)
    seeds_sm = _validate_seeds_sm(seeds_block, bundle=bundle, anchor_mode=runspecs.anchor_mode)
    seeds_elapsed_sm = _validate_elapsed_quarters_sm(seeds_block, bundle=bundle, anchor_mode=runspecs.anchor_mode)
    seeds_completed = _validate_completed_projects(scenario_dict.get("seeds"), bundle=bundle, anchor_mode=runspecs.anchor_mode)
    seeds_completed_sm = _validate_completed_projects_sm(scenario_dict.get("seeds"), bundle=bundle, anchor_mode=runspecs.anchor_mode)

    # SM-mode strictness
    if runspecs.anchor_mode == "sm":
        import pandas as pd
        if scenario_lists_sm_pairs:
            sm_df = pd.DataFrame(scenario_lists_sm_pairs, columns=["Sector", "Material"]).drop_duplicates()
        else:
            sm_df = getattr(bundle, "lists_sm", None)
            if sm_df is None or sm_df.empty:
                raise ValueError("SM-mode requires non-empty lists_sm (provide via scenario or inputs.json)")
            if not getattr(bundle, "lists_sm_explicit", False):
                raise ValueError("SM-mode requires lists_sm be explicitly provided (scenario or inputs.json), not derived")
        targeted_sm_params = {
            "anchor_start_year",
            "anchor_client_activation_delay",
            "anchor_lead_generation_rate",
            "lead_to_pc_conversion_rate",
            "project_generation_rate",
            "max_projects_per_pc",
            "project_duration",
            "projects_to_client_conversion",
            "initial_phase_duration",
            "ramp_phase_duration",
            "ATAM",
            "initial_requirement_rate",
            "initial_req_growth",
            "ramp_requirement_rate",
            "ramp_req_growth",
            "steady_requirement_rate",
            "steady_req_growth",
            "requirement_to_order_lag",
        }
        anchor_sm_df = getattr(bundle, "anchor_sm", None)
        if anchor_sm_df is None or anchor_sm_df.empty:
            raise ValueError("SM-mode requires anchor_params_sm with full coverage for all targeted parameters and pairs in lists_sm")
        available = {
            (str(r["Sector"]).strip(), str(r["Material"]).strip(), str(r["Param"]).strip())
            for _, r in anchor_sm_df.iterrows()
        }
        available |= _sm_constants_from_overrides(constants, bundle, targeted_sm_params)
        missing: list[str] = []
        for _, row in sm_df.iterrows():
            s = str(row["Sector"]).strip()
            m = str(row["Material"]).strip()
            for p in targeted_sm_params:
                if (s, m, p) not in available:
                    missing.append(f"({s}, {m}, {p})")
        if missing:
            preview = ", ".join(missing[:10]) + (" ..." if len(missing) > 10 else "")
            raise ValueError("SM-mode missing per-(sector, material) parameters for: " + preview)

    return Scenario(
        name=name,
        runspecs=runspecs,
        constants=constants,
        points=points,
        primary_map=pm_overrides or None,
        lists_sm=scenario_lists_sm_pairs or None,
        seeds_active_anchor_clients=seeds_active or None,
        seeds_elapsed_quarters=seeds_elapsed or None,
        seeds_direct_clients=seeds_direct or None,
        seeds_active_anchor_clients_sm=seeds_sm or None,
        seeds_elapsed_quarters_sm=seeds_elapsed_sm or None,
        seeds_completed_projects=seeds_completed or None,
        seeds_completed_projects_sm=seeds_completed_sm or None,
    )


def summarize_lists(bundle: Phase1Bundle) -> dict:
    """Return simple lists and mappings for UI dropdowns/context.

    Keys:
      - markets: list[str]
      - sectors: list[str]
      - materials: list[str]
      - sector_to_materials: dict[str, list[str]]
    """
    markets = (
        bundle.lists.markets_sectors_materials.get("Market", []).dropna().astype(str).unique().tolist()
        if hasattr(bundle.lists, "markets_sectors_materials")
        else []
    )
    return {
        "markets": markets,
        "sectors": list(bundle.lists.sectors),
        "materials": list(bundle.lists.materials),
        "sector_to_materials": dict(bundle.primary_map.sector_to_materials),
    }


__all__ = [
    "RunSpecs",
    "Scenario",
    "load_and_validate_scenario",
    "list_permissible_override_keys",
    "validate_scenario_dict",
    "summarize_lists",
]


def validate_overrides_against_model(model, scenario: Scenario) -> None:
    """Phase 11 tightening: ensure every override key maps to an existing model element.

    - For constants: each name must exist in `model.constants`.
    - For points: each lookup key must map to a converter name that exists in `model.converters`.
    Raises `ValueError` with actionable messages otherwise.
    """
    const_map = getattr(model, "constants", {})
    conv_map = getattr(model, "converters", {})

    # Check constants
    missing_constants = [name for name in scenario.constants.keys() if name not in const_map]

    # Check points by mapping lookup name -> converter name
    missing_points: list[str] = []
    for lookup_name in scenario.points.keys():
        if lookup_name.startswith("price_"):
            material = lookup_name[len("price_") :].replace("_", " ")
            conv_name = _price_conv_name(material)
        elif lookup_name.startswith("max_capacity_"):
            material = lookup_name[len("max_capacity_") :].replace("_", " ")
            conv_name = _cap_conv_name(material)
        else:
            # Unknown pattern – fail fast with hint
            missing_points.append(f"{lookup_name} (unknown lookup prefix; expected 'price_' or 'max_capacity_')")
            continue
        if conv_name not in conv_map:
            missing_points.append(f"{lookup_name} → converter '{conv_name}' not found in model")

    if missing_constants or missing_points:
        parts = []
        if missing_constants:
            parts.append("constants: " + ", ".join(missing_constants))
        if missing_points:
            parts.append("points: " + ", ".join(missing_points))
        raise ValueError("Override keys do not match built model elements: " + " | ".join(parts))


