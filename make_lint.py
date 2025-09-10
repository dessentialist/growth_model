#!/usr/bin/env python3
"""
Tiny lint/format harness to keep the repo tidy without imposing global configs.
Runs ruff (if installed) and black (if installed) in check mode; otherwise no-ops.

Also includes CSV to inputs.json extraction functionality.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> int:
    try:
        return subprocess.run(cmd, check=False).returncode
    except FileNotFoundError:
        return 0


def extract_csv_to_inputs() -> int:
    """
    Extract data from CSV files and create inputs.json.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Import the extraction script
        from extract_csv_to_inputs import main as extract_main
        extract_main()
        return 0
    except Exception as e:
        print(f"❌ Error during CSV extraction: {e}")
        return 1


def main() -> int:
    """
    Main function that handles both linting and CSV extraction.
    
    If --extract-csv is passed, runs CSV extraction instead of linting.
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--extract-csv":
        return extract_csv_to_inputs()
    
    # Default behavior: run linting
    paths = ["."]
    rc = 0
    if shutil.which("ruff"):
        rc |= run(["ruff", "check", *paths])
    if shutil.which("black"):
        rc |= run(["black", "--check", *paths])
    return rc


if __name__ == "__main__":
    sys.exit(main())
