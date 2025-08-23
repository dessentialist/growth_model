from __future__ import annotations

"""
Phase 13 — Multi‑Material Anchors: integration test

This test crafts a temporary `inputs.json` clone where a sector maps to two
materials. It verifies that:
- Per sector–material gateway converters exist
- Per sector–material anchor delivery flows are delayed by the sector lag
- Aggregated material delivery equals the sum over sectors
- KPI extractor attributes sector revenue as the sum over materials for that sector

We simplify dynamics by forcing FR=1, Price=1, and zeroing client requirements
so anchor deliveries pass through unmodified.
"""

import json
from pathlib import Path

import pytest

from BPTK_Py.modeling.simultaneousScheduler import SimultaneousScheduler

from src.phase1_data import load_phase1_inputs
from src.fff_growth_model import build_phase4_model
from src.naming import (
    agent_demand_sector_input,
    anchor_delivery_flow_sector_material,
    anchor_delivery_flow_material,
    price_converter,
)
from src.kpi_extractor import collect_kpis_for_step


def _load_inputs_json_dict(repo_root: Path) -> dict:
    with open(repo_root / "inputs.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _write_temp_inputs_json(tmp_path: Path, data: dict) -> Path:
    target = tmp_path / "inputs.json"
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return target


@pytest.mark.parametrize(
    "sector,mat_a,mat_b",
    [
        ("Semiconductors", "Silicon Carbide Powder", "UHT"),
    ],
)
def test_multi_material_anchor_sector(tmp_path: Path, sector: str, mat_a: str, mat_b: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    base = _load_inputs_json_dict(repo_root)

    # Extend primary_map: ensure `sector` maps to two materials (mat_a, mat_b)
    # Preserve existing mapping entries and inject an additional one if missing.
    entries = base.setdefault("primary_map", {}).setdefault(sector, [])
    have = {e.get("material") for e in entries}
    if mat_a not in have:
        entries.append({"material": mat_a, "start_year": 2025})
    if mat_b not in have:
        entries.append({"material": mat_b, "start_year": 2025})

    # Sanity: other_params, production, pricing must contain both materials
    for m in (mat_a, mat_b):
        assert m in base["other_params"]["lead_start_year"], f"Missing other params for {m}"
        assert m in base["production"], f"Missing production table for {m}"
        assert m in base["pricing"], f"Missing pricing table for {m}"

    inputs_path = _write_temp_inputs_json(tmp_path, base)

    # Build bundle and model (short horizon for speed)
    bundle = load_phase1_inputs(inputs_path)
    runspecs = type("RS", (), {"starttime": 2025.0, "stoptime": 2025.0 + 1.0, "dt": 0.25})()
    build = build_phase4_model(bundle, runspecs)
    model = build.model

    # Attach scheduler for stepping
    model.scheduler = SimultaneousScheduler()

    # Force simple conditions:
    # - Gateway inputs 10.0 for both materials for the chosen sector
    # - Zero client requirement by overriding its upstream converter to 0
    # - Capacity huge (FR -> 1). Achieve via large max_capacity_lookup
    # - Price = 1 for both materials
    for m in (mat_a, mat_b):
        # Gateways for the tested sector
        name_sm = agent_demand_sector_input(sector, m)
        model.converters[name_sm].equation = 10.0

        # Price = 1
        model.converters[price_converter(m)].equation = 1.0

        # Zero Client_Requirement by setting its input C*avg to 0 via a helper converter name
        # Known internal helper used in model build: C_times_avg_<m>
        helper = f"C_times_avg_{m.replace(' ', '_')}"
        if helper in model.converters:
            model.converters[helper].equation = 0.0

        # Huge capacity to ensure FR=1
        cap_name = f"max_capacity_lookup_{m.replace(' ', '_')}"
        if cap_name in model.converters:
            model.converters[cap_name].equation = 1e9

    # Run a few steps (4 quarters)
    for step_idx in range(0, 6):
        model.run_step(step_idx, collect_data=False)

    # Evaluation time after sector lag (Semiconductors lag = 0.5 years ⇒ 2 steps)
    t = 2025.0 + 0.25 * 4  # safely beyond lag

    # Per sector–material delivery flows should equal 10.0 (FR=1, delay passed)
    adf_a = float(model.evaluate_equation(anchor_delivery_flow_sector_material(sector, mat_a), t))
    adf_b = float(model.evaluate_equation(anchor_delivery_flow_sector_material(sector, mat_b), t))
    assert adf_a == pytest.approx(10.0, rel=0, abs=1e-6)
    assert adf_b == pytest.approx(10.0, rel=0, abs=1e-6)

    # Material-level aggregate equals sector flow (only one sector contributing in test)
    adf_mat_a = float(model.evaluate_equation(anchor_delivery_flow_material(mat_a), t))
    adf_mat_b = float(model.evaluate_equation(anchor_delivery_flow_material(mat_b), t))
    assert adf_mat_a == pytest.approx(10.0, rel=0, abs=1e-6)
    assert adf_mat_b == pytest.approx(10.0, rel=0, abs=1e-6)

    # KPI extractor: Revenue <sector> should sum across both materials (price=1)
    # Build sector→materials mapping from bundle
    sector_to_materials = bundle.primary_map.sector_to_materials

    # Provide minimal ABM metrics (zeros) to satisfy interface
    agent_metrics_by_step = [
        {
            "t": t,
            "active_by_sector": {},
            "inprogress_by_sector": {},
            "active_total": 0,
            "inprogress_total": 0,
        }
        for _ in range(12)
    ]

    kpis = collect_kpis_for_step(
        model=model,
        bundle=bundle,
        t=t,
        agents_by_sector={},
        sector_to_materials=sector_to_materials,
        step_idx=4,
        agent_metrics_by_step=agent_metrics_by_step,
    )

    assert kpis[f"Revenue {sector}"] == pytest.approx(20.0, rel=0, abs=1e-6)
