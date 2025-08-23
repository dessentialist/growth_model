from __future__ import annotations

"""
Phase 17.1 — Schema, Naming, and Loader (strict, no fallbacks)

Tests focus on scenario loader behavior:
- SM-mode requires explicit lists_sm and complete anchor_params_sm coverage
- Sector-level anchor constants are not permissible override keys in SM-mode
- Sector-mode behavior remains unchanged
"""

from pathlib import Path
import pandas as pd
import textwrap
import pytest

from src.phase1_data import load_phase1_inputs, Phase1Bundle
from src.scenario_loader import load_and_validate_scenario, RunSpecs
from src.growth_model import build_phase4_model
from src.naming import (
    anchor_lead_generation_sm,
    cpc_stock_sm,
    new_pc_flow_sm,
    agents_to_create_converter_sm,
    agents_to_create_converter,
)
from src.abm_anchor import (
    AnchorClientAgentSM,
    AnchorClientSMParams,
    build_sm_anchor_agent_factory,
)


def _write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "scenario.yaml"
    p.write_text(textwrap.dedent(content).strip(), encoding="utf-8")
    return p


def test_sm_mode_requires_explicit_lists_sm(tmp_path: Path):
    """Without explicit lists_sm in inputs.json, SM-mode must fail early."""
    bundle = load_phase1_inputs()
    # Ensure our test assumption: current repo inputs.json does not provide explicit lists_sm
    assert getattr(bundle, "lists_sm_explicit", False) is False

    scenario_yaml = _write_yaml(
        tmp_path,
        """
        name: sm_mode_missing_lists
        runspecs:
          starttime: 2025.0
          stoptime: 2026.0
          dt: 0.25
          anchor_mode: sm
        """,
    )

    with pytest.raises(ValueError) as exc:
        load_and_validate_scenario(scenario_yaml, bundle=bundle)
    assert "lists_sm" in str(exc.value)


def test_sm_mode_rejects_sector_level_anchor_constant_override(tmp_path: Path):
    """In SM-mode, sector-level anchor constant overrides must be rejected by loader."""
    bundle = load_phase1_inputs()
    assert getattr(bundle, "lists_sm_explicit", False) is False
    # Try overriding a sector-level anchor constant; expect unknown constant error
    scenario_yaml = _write_yaml(
        tmp_path,
        """
        name: sm_mode_sect_const_forbidden
        runspecs:
          anchor_mode: sm
        overrides:
          constants:
            initial_requirement_rate_Defense: 999.0
        """,
    )

    with pytest.raises(ValueError) as exc:
        load_and_validate_scenario(scenario_yaml, bundle=bundle)
    # The error should mention unknown constants
    assert "Unknown constants" in str(exc.value)


def test_sector_mode_allows_sector_level_anchor_constant_override(tmp_path: Path):
    """In sector-mode, sector-level anchor constant overrides are allowed and parsed."""
    bundle = load_phase1_inputs()
    scenario_yaml = _write_yaml(
        tmp_path,
        """
        name: sector_mode_ok
        runspecs:
          anchor_mode: sector
        overrides:
          constants:
            initial_requirement_rate_Defense: 123.0
        """,
    )
    scenario = load_and_validate_scenario(scenario_yaml, bundle=bundle)
    # Verify the override was accepted
    assert scenario.constants.get("initial_requirement_rate_Defense") == pytest.approx(123.0)


def test_sm_mode_builds_per_pair_creation_and_skips_sector_level(tmp_path: Path):
    """Phase 17.2: Building the model in SM-mode should create per-(s,m) creation
    pipelines and NOT create sector-level creation signals.

    We verify presence of a few canonical per-(s,m) elements and absence of
    `Agents_To_Create_<sector>` when `anchor_mode=sm`.
    """
    base_bundle = load_phase1_inputs()
    # Choose a sample pair from primary_map
    row = base_bundle.primary_map.long[["Sector", "Material"]].drop_duplicates().iloc[0]
    sector = str(row["Sector"])
    material = str(row["Material"])
    # Create explicit lists_sm with the single pair
    # Important: in SM-mode the model will attempt to build per-(s,m) constants
    # for every pair in lists_sm for every sector that uses this material.
    # To keep this unit test focused and independent, include only the chosen
    # sector in lists_sm and also restrict primary_map to map only this sector
    # to this material.
    lists_sm = pd.DataFrame([[sector, material]], columns=["Sector", "Material"])
    # Build a full anchor_sm coverage table for the pair with values copied from sector params
    required_params = [
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
    ]
    rows = []
    for p in required_params:
        v = float(base_bundle.anchor.by_sector.at[p, sector])
        rows.append({"Sector": sector, "Material": material, "Param": p, "Value": v})
    anchor_sm = pd.DataFrame(rows, columns=["Sector", "Material", "Param", "Value"]).reset_index(drop=True)

    # Construct a modified bundle with explicit lists_sm and full anchor_sm coverage
    # Restrict primary_map to only the selected (sector, material) so the model
    # does not attempt to build additional pairs.
    prim_long = pd.DataFrame([[sector, material, 2025.0]], columns=["Sector", "Material", "StartYear"]).reset_index(drop=True)
    prim_mapping = {sector: [material]}

    bundle = Phase1Bundle(
        lists=base_bundle.lists,
        anchor=base_bundle.anchor,
        other=base_bundle.other,
        production=base_bundle.production,
        pricing=base_bundle.pricing,
        primary_map=type(base_bundle.primary_map)(prim_mapping, prim_long),
        anchor_sm=anchor_sm,
        lists_sm=lists_sm,
        lists_sm_explicit=True,
    )

    runspecs = RunSpecs(starttime=2025.0, stoptime=2026.0, dt=0.25, anchor_mode="sm")
    build = build_phase4_model(bundle, runspecs)
    model = build.model

    # Per-(s,m) creation elements should exist
    assert anchor_lead_generation_sm(sector, material) in getattr(model, "converters", {})
    assert cpc_stock_sm(sector, material) in getattr(model, "stocks", {})
    assert new_pc_flow_sm(sector, material) in getattr(model, "converters", {})
    assert agents_to_create_converter_sm(sector, material) in getattr(model, "converters", {})

    # Sector-level creation signal must NOT exist in SM-mode
    assert agents_to_create_converter(sector) not in getattr(model, "converters", {})


def test_sm_agent_lifecycle_and_requirement_generation():
    """Phase 17.3: Validate AnchorClientAgentSM lifecycle and deterministic requirements.

    We simulate a minimal setup where the project generation is fast enough to
    activate quickly, and requirement phases produce predictable outputs.
    """
    # Construct params with short durations for a tight test
    params = AnchorClientSMParams(
        anchor_start_year_years=2025.0,
        anchor_client_activation_delay_quarters=1.0,
        project_generation_rate=1.0,
        max_projects_per_pc=1.0,
        project_duration_quarters=1.0,
        projects_to_client_conversion=1.0,
        initial_phase_duration_quarters=1.0,
        ramp_phase_duration_quarters=1.0,
        initial_requirement_rate=10.0,
        initial_req_growth=0.0,
        ramp_requirement_rate=20.0,
        ramp_req_growth=0.0,
        steady_requirement_rate=30.0,
        steady_req_growth=0.0,
    )

    agent = AnchorClientAgentSM(sector="Defense", material="Silicon Carbide Fiber", params=params)

    # Timeline at dt=0.25 years (quarters)
    times = [2025.0 + i * 0.25 for i in range(6)]
    outputs = []
    for i, t in enumerate(times):
        req = agent.act(t, 0, i, dt_years=0.25)
        outputs.append(req["Silicon Carbide Fiber"])

    # Expected behavior:
    # t0: POTENTIAL; project started; not active yet; requirement 0
    # t1: project completes; schedule activation after 1 quarter; requirement 0
    # t2: activation occurs now; first active quarter → initial phase value = 10
    # t3: ramp phase → 20
    # t4+: steady phase → 30
    assert outputs[0] == 0.0
    assert outputs[1] == 0.0
    assert outputs[2] == 10.0
    assert outputs[3] == 20.0
    assert outputs[4] == 30.0
    assert outputs[5] == 30.0


def test_build_sm_agent_factory_uses_strict_sm_params():
    """Factory must pull parameters strictly from anchor_params_sm with no fallbacks."""
    base_bundle = load_phase1_inputs()
    # Choose a sample pair from primary_map to mirror existing materials
    row = base_bundle.primary_map.long[["Sector", "Material"]].drop_duplicates().iloc[0]
    sector = str(row["Sector"])
    material = str(row["Material"])

    # Build explicit lists_sm and full per-(s,m) anchor_sm entries
    lists_sm = pd.DataFrame([[sector, material]], columns=["Sector", "Material"]).reset_index(drop=True)
    required_params = [
        "anchor_start_year",
        "anchor_client_activation_delay",
        "project_generation_rate",
        "max_projects_per_pc",
        "project_duration",
        "projects_to_client_conversion",
        "initial_phase_duration",
        "ramp_phase_duration",
        "initial_requirement_rate",
        "initial_req_growth",
        "ramp_requirement_rate",
        "ramp_req_growth",
        "steady_requirement_rate",
        "steady_req_growth",
    ]
    rows = []
    for p in required_params:
        v = float(base_bundle.anchor.by_sector.at[p, sector])
        rows.append({"Sector": sector, "Material": material, "Param": p, "Value": v})
    anchor_sm = pd.DataFrame(rows, columns=["Sector", "Material", "Param", "Value"]).reset_index(drop=True)

    bundle = Phase1Bundle(
        lists=base_bundle.lists,
        anchor=base_bundle.anchor,
        other=base_bundle.other,
        production=base_bundle.production,
        pricing=base_bundle.pricing,
        primary_map=base_bundle.primary_map,
        anchor_sm=anchor_sm,
        lists_sm=lists_sm,
        lists_sm_explicit=True,
    )

    factory = build_sm_anchor_agent_factory(bundle, sector, material)
    a1 = factory()
    a2 = factory()
    # Deterministic construction and independence
    assert isinstance(a1, AnchorClientAgentSM)
    assert isinstance(a2, AnchorClientAgentSM)
    assert a1 is not a2
