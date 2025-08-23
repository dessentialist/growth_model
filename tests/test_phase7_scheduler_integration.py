import unittest
from pathlib import Path

from BPTK_Py.modeling.simultaneousScheduler import SimultaneousScheduler

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from src.fff_growth_model import build_phase4_model, apply_scenario_overrides
from src.naming import (
    agent_demand_sector_input,
    agent_aggregated_demand,
    fulfillment_ratio,
    anchor_delivery_flow_material,
)


class TestPhase7SchedulerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_phase1_inputs(Path("Inputs"))
        cls.scenario = load_and_validate_scenario(Path("scenarios/baseline.yaml"), bundle=cls.bundle)

    def test_two_step_scheduler_with_gateway_updates(self):
        # Build model and apply overrides
        res = build_phase4_model(self.bundle, self.scenario.runspecs)
        model = res.model
        apply_scenario_overrides(model, self.scenario)

        # Attach scheduler as used by the runner
        model.scheduler = SimultaneousScheduler()

        # Pick first material present in lists and mapped to at least one sector
        material = None
        sectors_using_material = []
        for m in self.bundle.lists.materials:
            sectors_using_material = (
                self.bundle.primary_map.long[self.bundle.primary_map.long["Material"] == m]["Sector"]
                .astype(str)
                .unique()
                .tolist()
            )
            if sectors_using_material:
                material = m
                break

        self.assertIsNotNone(material, "No material with sector mapping found for scheduler test")

        # Times
        t0 = float(self.scenario.runspecs.starttime)
        t1 = t0 + float(self.scenario.runspecs.dt)

        # Step 0: set all per-sector inputs to 0.0 and step once
        for s in sectors_using_material:
            name_sm = agent_demand_sector_input(s, material)
            if name_sm in getattr(model, "converters", {}):
                model.converters[name_sm].equation = 0.0

        # Advance one step
        model.run_step(0, collect_data=False)

        # Aggregated demand at t0 should equal sum of inputs (0.0)
        name_agg = agent_aggregated_demand(material)
        agg0 = float(model.evaluate_equation(name_agg, t0))
        self.assertAlmostEqual(agg0, 0.0, places=12)

        # Fulfillment ratio is always within [0,1]
        name_fr = fulfillment_ratio(material)
        fr0 = float(model.evaluate_equation(name_fr, t0))
        self.assertGreaterEqual(fr0, 0.0)
        self.assertLessEqual(fr0, 1.0)

        # Step 1: set distinct gateway values and step again
        expected_sum = 0.0
        for idx, s in enumerate(sectors_using_material, start=1):
            name_sm = agent_demand_sector_input(s, material)
            if name_sm in getattr(model, "converters", {}):
                val = float(idx)
                model.converters[name_sm].equation = val
                expected_sum += val

        model.run_step(1, collect_data=False)

        # Aggregated demand at t1 should equal our sum of sector inputs
        agg1 = float(model.evaluate_equation(name_agg, t1))
        self.assertAlmostEqual(agg1, expected_sum, places=12)

        # Fulfillment ratio remains within bounds
        fr1 = float(model.evaluate_equation(name_fr, t1))
        self.assertGreaterEqual(fr1, 0.0)
        self.assertLessEqual(fr1, 1.0)

        # Anchor delivery flow is non-negative (we don't assert magnitude due to delays)
        name_adf_m = anchor_delivery_flow_material(material)
        adf1 = float(model.evaluate_equation(name_adf_m, t1))
        self.assertGreaterEqual(adf1, 0.0)


if __name__ == "__main__":
    unittest.main()
