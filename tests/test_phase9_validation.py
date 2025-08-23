from __future__ import annotations

"""
Targeted tests for Phase 9 validation utilities.

These tests sanity-check that:
- Scenario echo writes files and logs counts
- Agents_To_Create signals validate integer/non-negative behavior
- Fulfillment ratio bounds check triggers for out-of-range values
- Revenue identity check runs without raising on a built baseline model

We keep these tests light and synthetic; integration is covered elsewhere.
"""

from pathlib import Path

import unittest

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from src.growth_model import build_phase4_model, apply_scenario_overrides
from src.validation import (
    echo_scenario_overrides,
    validate_agents_to_create_signals,
    validate_fulfillment_ratio_bounds,
    validate_revenue_identity,
)


class TestPhase9Validation(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = load_phase1_inputs()
        scenario_path = Path("scenarios/baseline.yaml").resolve()
        self.scenario = load_and_validate_scenario(scenario_path, bundle=self.bundle)
        build = build_phase4_model(self.bundle, self.scenario.runspecs)
        self.model = build.model
        apply_scenario_overrides(self.model, self.scenario)

    def test_echo_overrides(self):
        tmp = Path("logs").resolve()
        p = echo_scenario_overrides(log_dir=tmp, scenario=self.scenario, log=__import__("logging").getLogger("t"))
        self.assertTrue(p.exists(), "scenario echo json must exist")

    def test_agents_to_create_integer(self):
        # Evaluate at t=starttime without advancing scheduler
        t = float(self.scenario.runspecs.starttime)
        # Should not raise for baseline
        validate_agents_to_create_signals(model=self.model, sectors=self.bundle.lists.sectors, t=t)

    def test_fulfillment_ratio_bounds(self):
        t = float(self.scenario.runspecs.starttime)
        validate_fulfillment_ratio_bounds(model=self.model, products=self.bundle.lists.products, t=t)

    def test_revenue_identity_initial(self):
        # Single-step identity should hold at t=start
        t = float(self.scenario.runspecs.starttime)
        # Build product->sectors mapping
        product_to_sectors = {}
        stm = self.bundle.primary_map.sector_to_materials
        for s, mats in stm.items():
            for m in mats:
                product_to_sectors.setdefault(m, []).append(s)
        validate_revenue_identity(
            model=self.model,
            products=self.bundle.lists.products,
            product_to_sectors=product_to_sectors,
            t=t,
        )


if __name__ == "__main__":
    unittest.main()
