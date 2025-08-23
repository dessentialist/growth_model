import unittest
from pathlib import Path

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario


class TestPhase11ScenarioVariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_phase1_inputs()

    def test_baseline_loads(self):
        p = Path("scenarios/baseline.yaml")
        scenario = load_and_validate_scenario(p, bundle=self.bundle)
        self.assertGreater(scenario.runspecs.stoptime, scenario.runspecs.starttime)

    def test_price_shock_loads_and_has_price_points(self):
        p = Path("scenarios/price_shock.yaml")
        scenario = load_and_validate_scenario(p, bundle=self.bundle)
        keys = list(scenario.points.keys())
        self.assertTrue(any(k.startswith("price_") for k in keys))

    def test_high_capacity_loads_and_has_capacity_points(self):
        p = Path("scenarios/high_capacity.yaml")
        scenario = load_and_validate_scenario(p, bundle=self.bundle)
        keys = list(scenario.points.keys())
        self.assertTrue(any(k.startswith("max_capacity_") for k in keys))


if __name__ == "__main__":
    unittest.main()
