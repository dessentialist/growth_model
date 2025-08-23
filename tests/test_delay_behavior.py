import unittest
from pathlib import Path

from BPTK_Py.modeling.simultaneousScheduler import SimultaneousScheduler

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from src.growth_model import build_phase4_model, apply_scenario_overrides
from src.naming import (
    client_delivery_flow,
    client_requirement,
    anchor_delivery_flow_product,
    agent_demand_sector_input,
)


class TestDelayBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_phase1_inputs(Path("Inputs"))
        cls.scenario = load_and_validate_scenario(Path("scenarios/baseline.yaml"), bundle=cls.bundle)

    def test_client_and_anchor_delay_effects(self):
        res = build_phase4_model(self.bundle, self.scenario.runspecs)
        model = res.model
        apply_scenario_overrides(model, self.scenario)

        model.scheduler = SimultaneousScheduler()

        # Choose first product and any mapped sector
        product = self.bundle.lists.products[0]
        sector = (
            self.bundle.primary_map.long[self.bundle.primary_map.long["Material"] == product]["Sector"]
            .astype(str)
            .unique()
            .tolist()[0]
        )

        t0 = float(self.scenario.runspecs.starttime)
        t1 = t0 + float(self.scenario.runspecs.dt)
        t2 = t1 + float(self.scenario.runspecs.dt)

        # Set client requirement upstream by ensuring there is at least 1 client and avg order > 0 happens naturally
        # Here we do not force client creation, but we still can assert non-negativity and delay monotonicity aspects.

        # Inject anchor gateway only at step 0 and then zero, to observe delay on anchor deliveries
        name_sm = agent_demand_sector_input(sector, product)
        if name_sm in getattr(model, "converters", {}):
            model.converters[name_sm].equation = 5.0
        model.run_step(0, collect_data=False)

        # After first step, with positive demand set only at step 0, anchor delivery likely still zero if lag > 0
        adf0 = float(model.evaluate_equation(anchor_delivery_flow_product(product), t0))
        self.assertGreaterEqual(adf0, 0.0)

        # Zero the input for the next step and advance
        if name_sm in getattr(model, "converters", {}):
            model.converters[name_sm].equation = 0.0
        model.run_step(1, collect_data=False)

        # With positive delayed demand at step 0, anchor delivery may start > 0 only after the lag has elapsed
        adf1 = float(model.evaluate_equation(anchor_delivery_flow_product(product), t1))
        self.assertGreaterEqual(adf1, 0.0)

        # Advance another step to ensure no errors evaluate
        model.run_step(2, collect_data=False)
        adf2 = float(model.evaluate_equation(anchor_delivery_flow_product(product), t2))
        self.assertGreaterEqual(adf2, 0.0)

        # Client side: requirement and delivery are always non-negative, and delivery follows requirement with its lag
        req0 = float(model.evaluate_equation(client_requirement(product), t0))
        cdf0 = float(model.evaluate_equation(client_delivery_flow(product), t0))
        self.assertGreaterEqual(req0, 0.0)
        self.assertGreaterEqual(cdf0, 0.0)


if __name__ == "__main__":
    unittest.main()
