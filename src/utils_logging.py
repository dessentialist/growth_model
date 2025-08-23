from __future__ import annotations

"""Logging utilities.

Set up a consistent logging configuration to both console and a file
in the `logs/` directory. This is intentionally simple and avoids
global side effects beyond configuring the root logger once per run.
"""

import logging
from pathlib import Path


def configure_logging(log_dir: Path, debug: bool = False) -> None:
    """Configure root logging for the application.

    - Creates the log directory if missing
    - Streams logs to both stdout and `logs/run.log`
    - Uses DEBUG level if `debug=True`, otherwise INFO
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "run.log"

    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        ],
    )


