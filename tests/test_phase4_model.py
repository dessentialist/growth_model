import unittest

from pathlib import Path

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from src.fff_growth_model import build_phase4_model, apply_scenario_overrides


class TestPhase4Model(unittest.TestCase):
    def setUp(self) -> None:
        # Load real CSVs from Inputs and baseline scenario
        self.bundle = load_phase1_inputs(Path("Inputs"))
        self.scenario = load_and_validate_scenario(
            Path("scenarios/baseline.yaml"), bundle=self.bundle
        )

    def test_build_and_apply_overrides(self):
        # Build model
        result = build_phase4_model(self.bundle, self.scenario.runspecs)
        model = result.model

        # Sanity: key converters exist for one typical material (access via model registries)
        material = self.bundle.lists.materials[0]
        price_name = f"Price_{material.replace(' ', '_')}"
        cap_name = f"max_capacity_lookup_{material.replace(' ', '_')}"

        self.assertIn(price_name, getattr(model, 'converters', {}))
        self.assertIn(cap_name, getattr(model, 'converters', {}))

        # Apply overrides (from baseline, should be a no-op or partial set)
        apply_scenario_overrides(model, self.scenario)

        # Ensure equations are set (function compiled), not raising
        model.converters[price_name].equation = model.converters[price_name].equation
        model.converters[cap_name].equation = model.converters[cap_name].equation


if __name__ == "__main__":
    unittest.main()


