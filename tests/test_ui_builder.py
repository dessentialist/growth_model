from __future__ import annotations

from pathlib import Path

from ui.services.builder import build_runner_command


def test_build_runner_command_defaults_to_baseline():
    """The builder should default to running the baseline preset when no
    explicit scenario path or preset name is passed. This ensures the
    UI can trigger a simple run without extra inputs."""
    rc = build_runner_command()
    cmd = rc.cmd
    assert "simulate_fff_growth.py" in cmd[1]
    # Defaults to preset baseline when neither scenario_path nor preset provided
    assert "--preset" in cmd and "baseline" in cmd


def test_build_runner_command_with_flags_and_scenario(tmp_path: Path):
    """When a scenario path is specified, the command should include that
    path and propagate optional flags for debug logs, plot generation, and
    optional KPI rows for SM diagnostics."""
    p = tmp_path / "foo.yaml"
    p.write_text("name: foo\n", encoding="utf-8")
    rc = build_runner_command(
        scenario_path=p,
        debug=True,
        visualize=True,
        kpi_sm_revenue_rows=True,
        kpi_sm_client_rows=True,
    )
    cmd = rc.cmd
    assert "--scenario" in cmd and str(p) in cmd
    assert "--debug" in cmd
    assert "--visualize" in cmd
    assert "--kpi-sm-revenue-rows" in cmd
    assert "--kpi-sm-client-rows" in cmd
