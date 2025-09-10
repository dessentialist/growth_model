import unittest
from pathlib import Path

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from src.growth_model import build_phase4_model, apply_scenario_overrides
from src.naming import price_converter_product, client_delivery_flow
from BPTK_Py.sddsl import functions as F


class TestPriceSensitivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_phase1_inputs(Path("Inputs"))

    def test_price_override_changes_price_equation(self):
        # Build baseline scenario
        text = {
            "name": "price-sensitivity",
            "runspecs": {"starttime": 2025.0, "stoptime": 2025.5, "dt": 0.25},
            "overrides": {"constants": {}, "points": {}},
        }
        import json
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp.write(json.dumps(text).encode("utf-8"))
            tmp.flush()
            scenario = load_and_validate_scenario(Path(tmp.name), bundle=self.bundle)

        try:
            res = build_phase4_model(self.bundle, scenario.runspecs)
            model = res.model
            apply_scenario_overrides(model, scenario)

            # Choose first product and override its price points upward
            material = self.bundle.lists.products[0]
            name_price = price_converter_product(material)
            self.assertIn(name_price, getattr(model, "converters", {}))

            # New simple price points
            new_points = [(2025.0, 9999.0), (2025.25, 9999.0), (2025.5, 9999.0)]
            model.converters[name_price].equation = F.lookup(F.time(), new_points)

            # Sanity: evaluate price at starttime equals our override
            p = float(model.evaluate_equation(name_price, 2025.0))
            self.assertAlmostEqual(p, 9999.0, places=6)

            # Client delivery remains defined and non-negative
            name_cdf = client_delivery_flow(material)
            cdf = float(model.evaluate_equation(name_cdf, 2025.0))
            self.assertGreaterEqual(cdf, 0.0)
        finally:
            Path(tmp.name).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
