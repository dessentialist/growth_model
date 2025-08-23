import json
import unittest
import tempfile
from pathlib import Path
import pandas as pd
import json

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from src.growth_model import build_phase4_model, apply_scenario_overrides
from src.kpi_extractor import RunGrid, extract_and_write_kpis
from src import io_paths


class TestCustomProductAndSectorNames(unittest.TestCase):
    def test_custom_names_propagate_to_output(self):
        # Determine original names from fixture
        base_data = json.loads(Path("inputs.json").read_text(encoding="utf-8"))
        old_sector = base_data["lists"][1]["Sector"][0]
        old_product = base_data["lists"][2]["Product"][0]
        new_sector = "AlphaSector"
        new_product = "BetaProduct"

        # Replace globally in JSON text to keep structure intact
        raw = Path("inputs.json").read_text(encoding="utf-8")
        raw = raw.replace(old_sector, new_sector).replace(old_product, new_product)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            inputs_path = tmp_path / "inputs.json"
            inputs_path.write_text(raw, encoding="utf-8")

            scenario_path = tmp_path / "scenario.yaml"
            scenario_path.write_text(
                "name: custom\n"
                "runspecs:\n  starttime: 2025.0\n  stoptime: 2025.25\n  dt: 0.25\n"
                "overrides: {}\n",
                encoding="utf-8",
            )

            bundle = load_phase1_inputs(inputs_path)
            scenario = load_and_validate_scenario(scenario_path, bundle=bundle)
            build = build_phase4_model(bundle, scenario.runspecs)
            model = build.model
            apply_scenario_overrides(model, scenario)

            # Redirect KPI output to temporary directory
            original_output = io_paths.OUTPUT_DIR
            io_paths.OUTPUT_DIR = tmp_path
            try:
                run_grid = RunGrid(start=float(scenario.runspecs.starttime), dt=float(scenario.runspecs.dt), num_steps=1)
                agents_by_sector = {s: [] for s in bundle.lists.sectors}
                sector_to_products = bundle.primary_map.sector_to_materials
                agent_metrics_by_step = [
                    {
                        "t": float(scenario.runspecs.starttime),
                        "active_by_sector": {s: 0 for s in bundle.lists.sectors},
                        "inprogress_by_sector": {s: 0 for s in bundle.lists.sectors},
                        "active_total": 0,
                        "inprogress_total": 0,
                    }
                ]
                out_path = extract_and_write_kpis(
                    model=model,
                    bundle=bundle,
                    run_grid=run_grid,
                    agents_by_sector=agents_by_sector,
                    sector_to_products=sector_to_products,
                    agent_metrics_by_step=agent_metrics_by_step,
                    kpi_values_by_step=[{}],
                )
            finally:
                io_paths.OUTPUT_DIR = original_output

            df = pd.read_csv(out_path)
            rows = set(df["Output Stocks"].astype(str))
            self.assertIn(f"Revenue {new_product}", rows)
            self.assertIn(f"Anchor Leads {new_sector}", rows)


if __name__ == "__main__":
    unittest.main()
