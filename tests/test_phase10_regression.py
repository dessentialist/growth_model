import unittest
from pathlib import Path
import logging
import math
import pandas as pd

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from simulate_fff_growth import run_stepwise


class TestPhase10BaselineRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load inputs and baseline scenario once for all tests
        cls.bundle = load_phase1_inputs(Path("Inputs"))
        cls.scenario = load_and_validate_scenario(Path("scenarios/baseline.yaml"), bundle=cls.bundle)

    def test_baseline_outputs_match_expected_layout_and_values_when_present(self):
        """
        Run the stepwise runner on the baseline scenario and compare the
        generated KPI CSV against `Inputs/Expected Output.csv`.

        Policy:
        - The expected CSV defines the row order and quarter labels.
        - If the expected row has numeric values present (non-NaN), compare
          the generated values to expected within a tight tolerance.
        - If the expected row cells are all empty/NaN, only enforce presence
          and alignment (structure check) without numeric comparison.
        """
        # 1) Execute the runner to generate the CSV
        log = logging.getLogger("runner-regression")
        run_stepwise(self.bundle, self.scenario, log=log)

        # 2) Locate files
        generated_path = Path("output/FFF_Growth_System_Complete_Results.csv")
        expected_path = Path("Inputs/Expected Output.csv")
        self.assertTrue(generated_path.exists(), "Generated KPI CSV not found")
        self.assertTrue(expected_path.exists(), "Expected KPI CSV not found")

        # 3) Load both CSVs
        df_gen = pd.read_csv(generated_path)
        df_exp = pd.read_csv(expected_path)

        # 4) Column label comparison (exact match)
        self.assertListEqual(
            df_gen.columns.tolist(),
            df_exp.columns.tolist(),
            "Column labels (quarters) differ from expected baseline",
        )

        # 5) Row label set and order comparison
        # The expected file may contain placeholder rows like
        # "Revenue {Sector}" or "Order Basket {Material}". Expand these
        # placeholders deterministically using the input lists to derive the
        # fully-qualified row sequence and compare to the generated rows.
        gen_rows = df_gen["Output Stocks"].astype(str).tolist()
        exp_rows_raw = df_exp["Output Stocks"].astype(str).tolist()

        sectors = list(self.bundle.lists.sectors)
        materials = list(self.bundle.lists.materials)

        expanded_exp_rows = []
        for label in exp_rows_raw:
            if "{Sector}" in label:
                base = label.replace("{Sector}", "{s}")
                expanded_exp_rows.extend([base.replace("{s}", s) for s in sectors])
            elif "{Material}" in label:
                base = label.replace("{Material}", "{m}")
                expanded_exp_rows.extend([base.replace("{m}", m) for m in materials])
            else:
                expanded_exp_rows.append(label)

        self.assertListEqual(
            gen_rows, expanded_exp_rows, "Row order/layout differs from expected baseline",
        )

        # 6) Value comparison when expected provides numbers
        data_cols = df_gen.columns.tolist()[1:]
        # Numeric comparisons must align with the expected file's row indices.
        # Iterate the raw expected rows and only compare when that row actually
        # contains numeric values. Placeholder rows (with {Sector}/{Material})
        # are empty in the expected file and are skipped.
        for idx, row_label in enumerate(exp_rows_raw):
            exp_vals = df_exp.iloc[idx][data_cols]

            # Determine if expected row contains any numeric values
            exp_has_numbers = pd.to_numeric(exp_vals, errors="coerce").notna().any()

            if not exp_has_numbers:
                # Structure-only assert done above; skip numeric comparison
                continue

            # Align generated row by exact label
            # This will raise if label is missing, surfacing a clear error
            match = df_gen[df_gen["Output Stocks"].astype(str) == row_label]
            self.assertFalse(match.empty, f"Generated CSV missing row '{row_label}' for numeric comparison")
            gen_vals = match.iloc[0][data_cols]

            # When expected values are present, compare with tolerance
            gen_num = pd.to_numeric(gen_vals, errors="coerce").fillna(0.0)
            exp_num = pd.to_numeric(exp_vals, errors="coerce").fillna(0.0)

            # Tight relative tolerance with small absolute floor
            for a, b in zip(gen_num.tolist(), exp_num.tolist()):
                # Allow small floating error; if both are near-zero, compare absolute
                if math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-10):
                    continue
                self.fail(
                    f"Numeric mismatch in row '{row_label}': generated {a} vs expected {b}"
                )


if __name__ == "__main__":
    unittest.main()


