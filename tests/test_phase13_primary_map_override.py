from __future__ import annotations

import json
from pathlib import Path

from src.phase1_data import load_phase1_inputs, apply_primary_map_overrides
from src.scenario_loader import load_and_validate_scenario


def test_primary_map_override_replaces_sector_products(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    base = json.loads((repo / "inputs.json").read_text(encoding="utf-8"))

    # Ensure Sector_One has one baseline mapping to start from
    base.setdefault("primary_map", {}).setdefault(
        "Sector_One", [{"product": "Product_One", "start_year": 2025}]
    )

    # Write temp inputs
    (tmp_path / "inputs.json").write_text(json.dumps(base), encoding="utf-8")

    # Create scenario YAML overriding Sector_One to two products
    scen_text = """
name: pm_override
runspecs:
  starttime: 2025.0
  stoptime: 2026.0
  dt: 0.25
overrides:
  primary_map:
    Sector_One:
      - { product: "Product_Two", start_year: 2026 }
      - { product: "Product_One", start_year: 2025 }
"""
    scen_path = tmp_path / "pm_override.yaml"
    scen_path.write_text(scen_text, encoding="utf-8")

    bundle = load_phase1_inputs(tmp_path)
    scenario = load_and_validate_scenario(scen_path, bundle=bundle)
    merged = apply_primary_map_overrides(bundle, scenario)

    # Sector_One should now have exactly these two products (order-insensitive)
    prods = set(merged.primary_map.sector_to_materials.get("Sector_One", []))
    assert prods == {"Product_Two", "Product_One"}

    # Long table rows for Sector_One should reflect the same set
    long_prods = set(
        merged.primary_map.long[merged.primary_map.long["Sector"] == "Sector_One"]["Material"].tolist()
    )
    assert long_prods == prods
