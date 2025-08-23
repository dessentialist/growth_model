from __future__ import annotations

import json
from pathlib import Path

from src.phase1_data import load_phase1_inputs, apply_primary_map_overrides
from src.scenario_loader import load_and_validate_scenario


def test_primary_map_override_replaces_sector_materials(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    base = json.loads((repo / "inputs.json").read_text(encoding="utf-8"))

    # Ensure Defense has one baseline mapping to start from
    base.setdefault("primary_map", {}).setdefault("Defense", [{"material": "Silicon Carbide Fiber", "start_year": 2025}])

    # Write temp inputs
    (tmp_path / "inputs.json").write_text(json.dumps(base), encoding="utf-8")

    # Create scenario YAML overriding Defense to two materials
    scen_text = """
name: pm_override
runspecs:
  starttime: 2025.0
  stoptime: 2026.0
  dt: 0.25
overrides:
  primary_map:
    Defense:
      - { material: "Silicon Nitride Fiber", start_year: 2026 }
      - { material: "Silicon Carbide Fiber", start_year: 2025 }
"""
    scen_path = tmp_path / "pm_override.yaml"
    scen_path.write_text(scen_text, encoding="utf-8")

    bundle = load_phase1_inputs(tmp_path)
    scenario = load_and_validate_scenario(scen_path, bundle=bundle)
    merged = apply_primary_map_overrides(bundle, scenario)

    # Defense should now have exactly these two materials (order-insensitive)
    mats = set(merged.primary_map.sector_to_materials.get("Defense", []))
    assert mats == {"Silicon Nitride Fiber", "Silicon Carbide Fiber"}

    # Long table rows for Defense should reflect the same set
    long_mats = set(merged.primary_map.long[merged.primary_map.long["Sector"] == "Defense"]["Material"].tolist())
    assert long_mats == mats


