from __future__ import annotations

import textwrap
from pathlib import Path

import pandas as pd

from src.phase1_data import load_phase1_inputs, apply_primary_map_overrides, apply_lists_sm_override
from src.scenario_loader import load_and_validate_scenario
from simulate_growth import run_stepwise


class _SilentLog:
    def info(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


def _read_kpi_csv_value(csv_path: Path, row_label: str) -> float:
    df = pd.read_csv(csv_path)
    assert "Output Stocks" in df.columns
    assert len(df.columns) >= 2
    row = df[df["Output Stocks"] == row_label]
    assert not row.empty
    # First data column after the label
    first_col = [c for c in df.columns if c != "Output Stocks"][0]
    return float(row.iloc[0][first_col])


def test_completed_projects_sector_mode(tmp_path: Path) -> None:
    # Set a known threshold via overrides; 1 step horizon
    scenario_text = textwrap.dedent(
        """
        name: completed_proj_sector
        runspecs:
          starttime: 2025.0
          stoptime: 2025.25
          dt: 0.25
        overrides:
          constants:
            projects_to_client_conversion_Defense: 3
        seeds:
          completed_projects:
            Defense: 7
        """
    ).strip()
    scenario_file = tmp_path / "completed_sector.yaml"
    scenario_file.write_text(scenario_text, encoding="utf-8")

    bundle = load_phase1_inputs()
    scenario = load_and_validate_scenario(scenario_file, bundle=bundle)
    bundle = apply_primary_map_overrides(bundle, scenario)

    out_csv = run_stepwise(bundle, scenario, log=_SilentLog())
    assert out_csv.exists()

    # floor(7 / 3) = 2 ACTIVE anchors at t0
    val = _read_kpi_csv_value(out_csv, "Anchor Clients Defense")
    assert int(val) == 2


def test_completed_projects_sm_mode(tmp_path: Path) -> None:
    # SM-mode requires explicit lists_sm; set threshold for the pair and seed backlog
    scenario_text = textwrap.dedent(
        """
        name: completed_proj_sm
        runspecs:
          starttime: 2025.0
          stoptime: 2025.25
          dt: 0.25
          anchor_mode: sm
        lists_sm:
          - { Sector: Defense, Material: Silicon Carbide Fiber }
        overrides:
          constants:
            projects_to_client_conversion_Defense_Silicon_Carbide_Fiber: 2
        seeds:
          completed_projects_sm:
            Defense:
              Silicon Carbide Fiber: 5
        """
    ).strip()
    scenario_file = tmp_path / "completed_sm.yaml"
    scenario_file.write_text(scenario_text, encoding="utf-8")

    bundle = load_phase1_inputs()
    scenario = load_and_validate_scenario(scenario_file, bundle=bundle)
    # Apply lists_sm override for strict SM-mode expectations
    bundle = apply_lists_sm_override(bundle, scenario)
    bundle = apply_primary_map_overrides(bundle, scenario)

    out_csv = run_stepwise(bundle, scenario, log=_SilentLog())
    assert out_csv.exists()

    # floor(5 / 2) = 2 ACTIVE anchors at t0
    val = _read_kpi_csv_value(out_csv, "Anchor Clients Defense")
    assert int(val) == 2
