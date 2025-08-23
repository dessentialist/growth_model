from __future__ import annotations

"""Minimal unit tests for UI helper APIs added through Phase 8.

These tests validate that permissible keys are generated and that an in-memory
scenario dict can be validated successfully with simple overrides.
"""

from pathlib import Path

import pytest

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import (
    list_permissible_override_keys,
    validate_scenario_dict,
)
from src.naming import price_lookup_name, max_capacity_lookup_name
from ui.state import UIState, PrimaryMapEntry
from ui.services.validation_client import get_bundle
from ui.services.builder import write_scenario_yaml


def test_permissible_keys_non_empty():
    bundle = load_phase1_inputs()
    data = list_permissible_override_keys(bundle, anchor_mode="sector")
    assert isinstance(data, dict)
    assert data["constants"] and data["points"], "Expected non-empty constants and points"


def test_points_names_include_first_material():
    bundle = load_phase1_inputs()
    mats = list(bundle.lists.materials)
    if not mats:
        pytest.skip("No materials listed in inputs.json")
    m = mats[0]
    data = list_permissible_override_keys(bundle, anchor_mode="sector")
    points = data["points"]
    assert price_lookup_name(m) in points
    assert max_capacity_lookup_name(m) in points


def test_validate_scenario_minimal_runspecs_only():
    bundle = load_phase1_inputs()
    scenario_dict = {
        "name": "friendly-kitten",
        "runspecs": {"starttime": 2025.0, "stoptime": 2026.0, "dt": 0.25, "anchor_mode": "sector"},
        "overrides": {"constants": {}, "points": {}},
    }
    s = validate_scenario_dict(bundle, scenario_dict)
    assert s.name == "friendly-kitten"
    assert s.runspecs.dt == 0.25


def test_validate_scenario_with_points_override():
    bundle = load_phase1_inputs()
    mats = list(bundle.lists.materials)
    if not mats:
        pytest.skip("No materials to build a points override")
    m = mats[0]
    pl = price_lookup_name(m)
    scenario_dict = {
        "name": "playful-puppy",
        "runspecs": {"starttime": 2025.0, "stoptime": 2026.0, "dt": 0.25},
        "overrides": {"constants": {}, "points": {pl: [[2025.0, 10.0], [2025.5, 10.0]]}},
    }
    s = validate_scenario_dict(bundle, scenario_dict)
    assert pl in s.points
def test_validate_with_primary_map_and_seeds(tmp_path):
    bundle = load_phase1_inputs()
    mats = list(bundle.lists.materials)
    secs = list(bundle.lists.sectors)
    if not mats or not secs:
        pytest.skip("Insufficient lists to construct primary map or seeds")
    m = mats[0]
    sct = secs[0]
    # Build UI state
    ui_state = UIState()
    ui_state.primary_map.by_sector[sct] = [PrimaryMapEntry(material=m, start_year=2026.0)]
    ui_state.seeds.active_anchor_clients[sct] = 2
    ui_state.seeds.elapsed_quarters[sct] = 4
    ui_state.seeds.direct_clients[m] = 3
    scenario_dict = ui_state.to_scenario_dict_normalized()
    # Validate
    s = validate_scenario_dict(bundle, scenario_dict)
    assert s.primary_map is not None
    assert s.seeds_active_anchor_clients is not None
    # Write YAML to a temp location to ensure writer works
    yaml_path = tmp_path / "temp_scenario.yaml"
    written = write_scenario_yaml(scenario_dict, yaml_path)
    assert written.exists()



def test_validate_scenario_points_strictly_increasing_years():
    bundle = load_phase1_inputs()
    mats = list(bundle.lists.materials)
    if not mats:
        pytest.skip("No materials to build a points override")
    m = mats[0]
    pl = price_lookup_name(m)
    scenario_dict = {
        "name": "grumpy-hamster",
        "runspecs": {"starttime": 2025.0, "stoptime": 2026.0, "dt": 0.25},
        "overrides": {"constants": {}, "points": {pl: [[2025.0, 10.0], [2025.0, 11.0]]}},
    }
    with pytest.raises(ValueError):
        _ = validate_scenario_dict(bundle, scenario_dict)


