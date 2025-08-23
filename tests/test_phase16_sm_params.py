from pathlib import Path

import pytest

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario, RunSpecs
from src.fff_growth_model import build_phase4_model
from src.naming import anchor_constant_sm


def test_phase16_model_creates_sm_requirement_to_order_lag_constant(tmp_path: Path):
    bundle = load_phase1_inputs()
    # Pick a known (sector, material) from primary_map
    assert not bundle.primary_map.long.empty, "Expected primary_map to be non-empty for this test"
    row = bundle.primary_map.long.iloc[0]
    sector = str(row["Sector"])
    material = str(row["Material"])

    # Build model with default runspecs (use Scenario defaults indirectly)
    runspecs = RunSpecs(starttime=2025.0, stoptime=2032.0, dt=0.25)
    build = build_phase4_model(bundle, runspecs)
    model = build.model

    # The per-(s,m) lag constant must exist regardless of whether anchor_params_sm was provided
    name_sm = anchor_constant_sm("requirement_to_order_lag", sector, material)
    assert name_sm in getattr(model, "constants", {}), f"Missing SM constant: {name_sm}"


def test_phase16_scenario_loader_accepts_sm_constant_override(tmp_path: Path):
    bundle = load_phase1_inputs()
    # Choose a sector, material from the SM universe (lists_sm if present, else primary_map)
    sm_df = getattr(bundle, "lists_sm", None)
    if sm_df is None or sm_df.empty:
        sm_df = bundle.primary_map.long[["Sector", "Material"]].drop_duplicates()
    row = sm_df.iloc[0]
    sector = str(row["Sector"]) 
    material = str(row["Material"]) 

    # Compose a scenario YAML with a per-(s,m) override for a targeted param
    const_key = anchor_constant_sm("requirement_to_order_lag", sector, material)
    scenario_text = f"""
name: sm_override_test
runspecs:
  starttime: 2025.0
  stoptime: 2032.0
  dt: 0.25
overrides:
  constants:
    {const_key}: 3.5
"""
    path = tmp_path / "sm_override_test.yaml"
    path.write_text(scenario_text)

    scenario = load_and_validate_scenario(path, bundle=bundle)
    # Expect the constant to be accepted and normalized to float
    assert pytest.approx(3.5) == scenario.constants[const_key]


