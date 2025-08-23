from __future__ import annotations

from pathlib import Path

import pytest


def test_phase12_generate_plots_smoke(tmp_path: Path):
    """Smoke test: generate plots from the baseline results CSV if present.

    This test is permissive: if the CSV is not present, it is skipped.
    When present, it imports the plotting module and verifies PNG files
    are created under `output/plots/` without raising exceptions.
    """
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output"
    csv_path = output_dir / "Growth_System_Complete_Results.csv"
    if not csv_path.exists():
        pytest.skip("Results CSV not found; run simulate_growth.py first")

    from viz.plots import generate_all_plots_from_csv

    out_paths = generate_all_plots_from_csv(csv_path)
    assert out_paths, "No plots were generated"
    for p in out_paths:
        assert p.exists(), f"Plot not created: {p}"
        assert p.stat().st_size > 0, f"Plot file is empty: {p}"
