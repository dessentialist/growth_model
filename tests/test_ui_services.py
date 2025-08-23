from __future__ import annotations

import os
from pathlib import Path

from ui.services.builder import build_runner_command, find_latest_results_csv


def test_build_runner_command_preset_only():
	rc = build_runner_command(preset="baseline", debug=True, visualize=False)
	assert "--preset" in rc.cmd
	assert "baseline" in rc.cmd
	assert "--debug" in rc.cmd


def test_find_latest_results_csv_empty(tmp_path: Path, monkeypatch):
	# Point OUTPUT_DIR to temp by faking env and project root structure is not needed here
	out_dir = tmp_path / "output"
	out_dir.mkdir(parents=True, exist_ok=True)
	# Create two dummy files
	p1 = out_dir / "FFF_Growth_System_Complete_Results.csv"
	p2 = out_dir / "FFF_Growth_System_Complete_Results_baseline.csv"
	p1.write_text("Output Stocks,2025Q1\nRevenue,0\n")
	p2.write_text("Output Stocks,2025Q1\nRevenue,1\n")
	# Use function directly by temporarily changing CWD so OUTPUT_DIR resolves
	cwd = os.getcwd()
	try:
		os.chdir(tmp_path)
		latest = find_latest_results_csv()
		assert latest is not None
		assert latest.exists()
	finally:
		os.chdir(cwd)