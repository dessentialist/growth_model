import json
import unittest
from pathlib import Path

from src.phase1_data import load_phase1_inputs, parse_json_to_bundle, Phase1Bundle


class TestPhase1JSONLoading(unittest.TestCase):
    def test_load_json_exists(self):
        # Default path points at project-root inputs.json
        bundle = load_phase1_inputs()
        self.assertIsInstance(bundle, Phase1Bundle)
        # Basic invariants from JSON fixture
        self.assertGreaterEqual(len(bundle.lists.sectors), 1)
        self.assertGreaterEqual(len(bundle.lists.products), 1)

    def test_parse_json_to_bundle_direct(self):
        data = json.loads(Path("inputs.json").read_text(encoding="utf-8"))
        bundle = parse_json_to_bundle(data)
        self.assertIsInstance(bundle, Phase1Bundle)
        # Ensure long tables have expected columns
        self.assertTrue(set(["Year", "Material", "Capacity"]).issubset(set(bundle.production.long.columns)))
        self.assertTrue(set(["Year", "Material", "Price"]).issubset(set(bundle.pricing.long.columns)))

    def test_us_only_market_enforced(self):
        # Load and ensure 'US' presence is validated
        bundle = load_phase1_inputs()
        # The validate_coverage call inside loader would raise if 'US' missing
        self.assertIn("US", set(bundle.lists.markets_sectors_materials.get("Market", []).unique()))

    def test_missing_lists_key_rejected(self):
        # Create a minimal invalid JSON structure without 'lists'
        bad = {
            "anchor_params": {},
            "other_params": {},
            "production": {},
            "pricing": {},
            "primary_map": {},
        }
        tmp = Path("inputs_bad.json")
        try:
            tmp.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_phase1_inputs(tmp)
        finally:
            if tmp.exists():
                tmp.unlink()

    def test_duplicate_product_names_rejected(self):
        data = {
            "lists": [
                {"Market": ["US"]},
                {"Sector": ["Defense"]},
                {"Product": ["Foo", "Foo"]},
            ],
            "anchor_params": {},
            "other_params": {},
            "production": {},
            "pricing": {},
            "primary_map": {},
        }
        with self.assertRaises(ValueError):
            parse_json_to_bundle(data)


if __name__ == "__main__":
    unittest.main()
