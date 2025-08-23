import json
from pathlib import Path
import tempfile
import unittest

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario


class TestScenarioLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load real Phase 1 bundle from provided CSVs so that permissible keys
        # reflect the actual sectors/materials in the Inputs directory.
        cls.bundle = load_phase1_inputs()

    def _write_temp(self, text: str, suffix: str) -> Path:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(text.encode("utf-8"))
        tmp.flush()
        tmp.close()
        return Path(tmp.name)

    def test_valid_yaml_minimal(self):
        p = self._write_temp(
            """
name: testy
runspecs:
  starttime: 2026.0
  stoptime: 2030.0
  dt: 0.25
overrides: {}
            """,
            ".yaml",
        )
        try:
            scenario = load_and_validate_scenario(p, bundle=self.bundle)
            self.assertEqual(scenario.name, "testy")
            self.assertEqual(scenario.runspecs.starttime, 2026.0)
            self.assertEqual(scenario.runspecs.dt, 0.25)
            self.assertFalse(scenario.constants)
            self.assertFalse(scenario.points)
        finally:
            p.unlink(missing_ok=True)

    def test_defaults_when_runspecs_missing(self):
        p = self._write_temp(
            """
name: defaults
overrides: {}
            """,
            ".yaml",
        )
        try:
            scenario = load_and_validate_scenario(p, bundle=self.bundle)
            self.assertEqual(scenario.runspecs.starttime, 2025.0)
            self.assertEqual(scenario.runspecs.stoptime, 2032.0)
            self.assertEqual(scenario.runspecs.dt, 0.25)
        finally:
            p.unlink(missing_ok=True)

    def test_unknown_constant_raises(self):
        p = self._write_temp(
            """
name: bad-keys
overrides:
  constants:
    not_a_real_parameter: 1.23
            """,
            ".yaml",
        )
        try:
            with self.assertRaises(ValueError):
                load_and_validate_scenario(p, bundle=self.bundle)
        finally:
            p.unlink(missing_ok=True)

    def test_points_validation_and_sorting(self):
        # Use an actual material from Lists.csv to ensure the lookup name is permissible
        material = self.bundle.lists.materials[0]
        # price_<material> must be accepted and sorted
        lookup_name = f"price_{material.replace(' ', '_')}"
        text = {
            "name": "points-test",
            "overrides": {
                "points": {
                    lookup_name: [[2027.0, 10], [2025.0, 5], [2026.0, 7]],
                }
            },
        }
        p = self._write_temp(json.dumps(text), ".json")
        try:
            scenario = load_and_validate_scenario(p, bundle=self.bundle)
            pts = scenario.points[lookup_name]
            self.assertEqual(pts, [(2025.0, 5.0), (2026.0, 7.0), (2027.0, 10.0)])
        finally:
            p.unlink(missing_ok=True)

    def test_non_increasing_points_rejected(self):
        material = self.bundle.lists.materials[0]
        lookup_name = f"max_capacity_{material.replace(' ', '_')}"
        text = {
            "name": "points-bad",
            "overrides": {
                "points": {
                    lookup_name: [[2025.0, 1], [2025.0, 2]],
                }
            },
        }
        p = self._write_temp(json.dumps(text), ".json")
        try:
            with self.assertRaises(ValueError):
                load_and_validate_scenario(p, bundle=self.bundle)
        finally:
            p.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
