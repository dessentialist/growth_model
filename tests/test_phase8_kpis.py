import unittest
from pathlib import Path
import pandas as pd

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from src.fff_growth_model import build_phase4_model, apply_scenario_overrides
from src.kpi_extractor import RunGrid, extract_and_write_kpis


class TestPhase8KPIExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_phase1_inputs(Path("Inputs"))
        cls.scenario = load_and_validate_scenario(Path("scenarios/baseline.yaml"), bundle=cls.bundle)

    def test_extract_and_write_kpis_shape(self):
        res = build_phase4_model(self.bundle, self.scenario.runspecs)
        model = res.model
        apply_scenario_overrides(model, self.scenario)

        # Minimal agents dict (no agents created) is valid
        agents_by_sector = {s: [] for s in self.bundle.lists.sectors}
        sector_to_materials = self.bundle.primary_map.sector_to_materials

        start = float(self.scenario.runspecs.starttime)
        dt = float(self.scenario.runspecs.dt)
        num_steps = int(round((float(self.scenario.runspecs.stoptime) - start) / dt))
        run_grid = RunGrid(start=start, dt=dt, num_steps=num_steps)

        # Provide zeroed per-step ABM metrics to align with stricter KPI API
        steps_to_emit = num_steps
        agent_metrics_by_step = []
        for i in range(steps_to_emit):
            agent_metrics_by_step.append(
                {
                    "t": start + dt * i,
                    "active_by_sector": {s: 0 for s in self.bundle.lists.sectors},
                    "inprogress_by_sector": {s: 0 for s in self.bundle.lists.sectors},
                    "active_total": 0,
                    "inprogress_total": 0,
                }
            )

        out_path = extract_and_write_kpis(
            model=model,
            bundle=self.bundle,
            run_grid=run_grid,
            agents_by_sector=agents_by_sector,
            sector_to_materials=sector_to_materials,
            agent_metrics_by_step=agent_metrics_by_step,
            # Provide empty per-step KPI snapshots to exercise strict path
            kpi_values_by_step=[{} for _ in range(steps_to_emit)],
        )

        self.assertTrue(out_path.exists(), "CSV file not written")
        df = pd.read_csv(out_path)
        # 1 label + num_steps columns
        self.assertEqual(1 + num_steps, df.shape[1])
        # Ensure some canonical rows are present
        rows = set(df["Output Stocks"].astype(str))
        self.assertIn("Revenue", rows)
        self.assertIn("Order Delivery", rows)
        self.assertIn("Anchor Leads", rows)


if __name__ == "__main__":
    unittest.main()


