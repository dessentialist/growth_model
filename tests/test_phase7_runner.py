import unittest
from pathlib import Path

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from src.fff_growth_model import build_phase4_model, apply_scenario_overrides
from src.naming import agents_to_create_converter, agent_demand_sector_input


class TestPhase7RunnerScaffolding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_phase1_inputs(Path("Inputs"))
        cls.scenario = load_and_validate_scenario(Path("scenarios/baseline.yaml"), bundle=cls.bundle)

    def test_model_build_and_gateways_updatable(self):
        # Build model and apply overrides
        res = build_phase4_model(self.bundle, self.scenario.runspecs)
        model = res.model
        apply_scenario_overrides(model, self.scenario)

        # Pick any sector-material pair from mapping
        row = self.bundle.primary_map.long.iloc[0]
        sector = str(row.Sector)
        material = str(row.Material)

        # Agent creation signal should be present and evaluable at start time
        name_to_create = agents_to_create_converter(sector)
        k0 = int(model.evaluate_equation(name_to_create, self.scenario.runspecs.starttime))
        self.assertGreaterEqual(k0, 0)

        # Update sector-material gateway numeric value and evaluate at next time
        name_sm = agent_demand_sector_input(sector, material)
        if name_sm in getattr(model, "converters", {}):
            model.converters[name_sm].equation = 1.23
        # Re-evaluate creation signal at next time step (no scheduler dependency)
        t_next = self.scenario.runspecs.starttime + self.scenario.runspecs.dt
        k1 = int(model.evaluate_equation(name_to_create, t_next))
        self.assertGreaterEqual(k1, 0)


if __name__ == "__main__":
    unittest.main()
