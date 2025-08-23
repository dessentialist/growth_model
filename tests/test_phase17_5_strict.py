from __future__ import annotations

"""
Phase 17.5 — Strict Enforcement (No Fallbacks, No Simplifications)

Negative tests to ensure:
- SM-mode requires full per-(sector, material) coverage for all targeted anchor parameters
- Sector-level seeding is rejected in SM-mode
- Unknown per-(s,m) override constants are rejected
"""

from pathlib import Path
import pandas as pd
import pytest
import textwrap

from src.phase1_data import load_phase1_inputs, Phase1Bundle
from src.scenario_loader import load_and_validate_scenario, RunSpecs
from src.growth_model import build_phase4_model


def _write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "scenario.yaml"
    p.write_text(textwrap.dedent(content).strip(), encoding="utf-8")
    return p


def test_sm_mode_partial_anchor_params_sm_coverage_fails_in_loader(tmp_path: Path):
    """Provide explicit lists_sm and anchor_params_sm missing one required param → error."""
    base = load_phase1_inputs()
    # pick a sample pair from primary_map
    row = base.primary_map.long[["Sector", "Material"]].drop_duplicates().iloc[0]
    sector = str(row["Sector"])
    material = str(row["Material"])

    # Build inputs.json-like explicit lists_sm via scenario (loader checks only scenario/runspecs/overrides/seeds)
    # The loader derives permissible constants from bundle; we simulate SM-mode by setting anchor_mode.
    # Compose a scenario with SM-mode and no overrides; loader should still validate anchor_sm coverage via bundle.

    # Create a modified bundle with explicit lists_sm and PARTIAL anchor_sm (missing 'steady_req_growth')
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
        # intentionally omit "steady_req_growth",
        "requirement_to_order_lag",
    ]
    rows = []
    for p in required_params:
        v = float(base.anchor.by_sector.at[p, sector])
        rows.append({"Sector": sector, "Material": material, "Param": p, "Value": v})
    anchor_sm = pd.DataFrame(rows, columns=["Sector", "Material", "Param", "Value"]).reset_index(drop=True)
    lists_sm = pd.DataFrame([[sector, material]], columns=["Sector", "Material"]).reset_index(drop=True)

    bundle = Phase1Bundle(
        lists=base.lists,
        anchor=base.anchor,
        other=base.other,
        production=base.production,
        pricing=base.pricing,
        primary_map=base.primary_map,
        anchor_sm=anchor_sm,
        lists_sm=lists_sm,
        lists_sm_explicit=True,
    )

    # Write a minimal SM-mode scenario
    scenario_yaml = _write_yaml(
        tmp_path,
        """
        name: sm_partial
        runspecs:
          starttime: 2025.0
          stoptime: 2026.0
          dt: 0.25
          anchor_mode: sm
        """,
    )

    # Loader should detect missing (s,m,param) coverage and raise
    with pytest.raises(ValueError) as exc:
        load_and_validate_scenario(scenario_yaml, bundle=bundle)
    assert "SM-mode missing per-(sector, material) parameters" in str(exc.value)


def test_sm_mode_model_build_raises_on_missing_sm_param():
    """Direct build in SM-mode must raise if anchor_sm lacks a required (s,m,param) triple."""
    base = load_phase1_inputs()
    row = base.primary_map.long[["Sector", "Material"]].drop_duplicates().iloc[0]
    sector = str(row["Sector"])
    material = str(row["Material"])

    # Provide explicit lists_sm but EMPTY anchor_sm → model build should fail when creating constants
    lists_sm = pd.DataFrame([[sector, material]], columns=["Sector", "Material"]).reset_index(drop=True)
    bundle = Phase1Bundle(
        lists=base.lists,
        anchor=base.anchor,
        other=base.other,
        production=base.production,
        pricing=base.pricing,
        primary_map=base.primary_map,
        anchor_sm=pd.DataFrame(columns=["Sector", "Material", "Param", "Value"]),
        lists_sm=lists_sm,
        lists_sm_explicit=True,
    )
    runspecs = RunSpecs(starttime=2025.0, stoptime=2026.0, dt=0.25, anchor_mode="sm")

    with pytest.raises(ValueError) as exc:
        build_phase4_model(bundle, runspecs)
    assert "SM-mode requires anchor_params_sm" in str(exc.value)


def test_sm_mode_rejects_sector_seeds_in_loader(tmp_path: Path):
    """Sector-level seeds must be rejected when anchor_mode=sm."""
    base = load_phase1_inputs()
    scenario_yaml = _write_yaml(
        tmp_path,
        """
        name: sm_seeds_sector_forbidden
        runspecs:
          anchor_mode: sm
        seeds:
          active_anchor_clients:
            Defense: 3
        """,
    )
    with pytest.raises(ValueError) as exc:
        load_and_validate_scenario(scenario_yaml, bundle=base)
    assert "prohibits seeds.active_anchor_clients" in str(exc.value)


def test_sm_mode_unknown_per_sm_override_rejected(tmp_path: Path):
    """An override for a (s,m) pair not present in lists_sm or primary_map must be rejected as unknown constant."""
    base = load_phase1_inputs()
    # Choose a sector/material that likely exists and modify the material name slightly to ensure mismatch
    sector = base.lists.sectors[0]
    bad_material_key = "Nonexistent_Material_For_SM_Override"
    scenario_yaml = _write_yaml(
        tmp_path,
        f"""
        name: sm_unknown_override
        runspecs:
          anchor_mode: sm
        overrides:
          constants:
            anchor_start_year_{sector.replace(' ', '_')}_{bad_material_key}: 2025.0
        """,
    )
    with pytest.raises(ValueError) as exc:
        load_and_validate_scenario(scenario_yaml, bundle=base)
    assert "Unknown constants" in str(exc.value)
