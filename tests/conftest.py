"""
Pytest configuration for ensuring the project root is on sys.path.

This allows test modules to import the in-repo package layout like:
    from src.phase1_data import load_phase1_inputs

Without relying on external environment variables.
"""

import os
import sys

# Insert the repository root (one directory up from tests/) at the
# beginning of sys.path to prioritize local modules over site-packages.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
