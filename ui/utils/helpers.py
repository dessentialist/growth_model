from __future__ import annotations

"""General-purpose helpers for the UI."""

from typing import Iterable, List


def ensure_unique_sorted(items: Iterable[str]) -> List[str]:
    """Return a unique, sorted list of strings."""
    return sorted(dict.fromkeys(items))


