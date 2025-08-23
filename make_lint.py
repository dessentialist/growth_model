#!/usr/bin/env python3
"""
Tiny lint/format harness to keep the repo tidy without imposing global configs.
Runs ruff (if installed) and black (if installed) in check mode; otherwise no-ops.
"""
from __future__ import annotations

import shutil
import subprocess
import sys


def run(cmd: list[str]) -> int:
    try:
        return subprocess.run(cmd, check=False).returncode
    except FileNotFoundError:
        return 0


def main() -> int:
    paths = ["."]
    rc = 0
    if shutil.which("ruff"):
        rc |= run(["ruff", "check", *paths])
    if shutil.which("black"):
        rc |= run(["black", "--check", *paths])
    return rc


if __name__ == "__main__":
    sys.exit(main())
