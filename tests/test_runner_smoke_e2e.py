import tempfile
import unittest
from pathlib import Path
import logging

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from simulate_fff_growth import run_stepwise


class TestRunnerSmokeE2E(unittest.TestCase):
    def test_runner_completes_short_horizon(self):
        bundle = load_phase1_inputs(Path("Inputs"))

        # Short horizon scenario (two steps) with no overrides
        text = """
        name: smoke
        runspecs:
          starttime: 2025.0
          stoptime: 2025.5
          dt: 0.25
        overrides: {}
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as tmp:
            tmp.write(text.encode("utf-8"))
            tmp.flush()
            scenario = load_and_validate_scenario(Path(tmp.name), bundle=bundle)

        try:
            log = logging.getLogger("runner-smoke")
            run_stepwise(bundle, scenario, log=log)
        finally:
            Path(tmp.name).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
