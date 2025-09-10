from __future__ import annotations

"""Scenario service: load, save, and list scenarios.

This service uses `src.io_paths.SCENARIOS_DIR` for paths and integrates
with `src.scenario_loader` for validation consistency. All I/O is
localized here to keep UI components free of filesystem concerns.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Any
import yaml

from src.io_paths import SCENARIOS_DIR, LOGS_DIR
from src.phase1_data import load_phase1_inputs
from src.scenario_loader import validate_scenario_dict, list_permissible_override_keys, summarize_lists
import json


class ScenarioService:
    """High-level scenario file operations."""

    def __init__(self, scenarios_dir: Path | None = None) -> None:
        self.scenarios_dir = scenarios_dir or SCENARIOS_DIR
        self.scenarios_dir.mkdir(parents=True, exist_ok=True)

    def load_scenario(self, name: str) -> Dict:
        """Load a scenario YAML by name without extension."""
        path = self.scenarios_dir / f"{name}.yaml"
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def save_scenario(self, data: Dict, name: str) -> Path:
        """Save a scenario dict to YAML and return the saved path."""
        path = self.scenarios_dir / f"{name}.yaml"
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        return path

    def list_scenarios(self) -> List[str]:
        """List scenario basenames (without .yaml)."""
        return sorted(p.stem for p in self.scenarios_dir.glob("*.yaml"))

    def validate_scenario(self, data: Dict) -> Tuple[bool, List[str]]:
        """Validate a scenario dict via backend validator, return (ok, errors).

        Loads the Phase 1 bundle from inputs.json and passes it to the
        backend validator to ensure name coverage checks use real inputs.
        """
        try:
            bundle = load_phase1_inputs()
            validate_scenario_dict(bundle, data)  # raises on error
            return True, []
        except Exception as exc:  # surface message only
            return False, [str(exc)]

    def validate_scenario_lenient_sm(self, data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate a scenario dict but treat orphan SM constants as informational.

        - In SM mode, constants targeting (sector, product) pairs not in lists_sm
          (or derived from primary_map) are temporarily dropped for validation and
          returned as a list for UI display. Other validation errors are surfaced.
        - In sector mode, behaves like strict validation.

        Returns (ok, errors, orphan_constants).
        """
        try:
            bundle = load_phase1_inputs()
        except Exception as exc:
            return False, [f"Failed to load inputs.json: {exc}"], []

        orphan_constants: List[str] = []

        runspecs = (data or {}).get("runspecs", {}) or {}
        anchor_mode = str(runspecs.get("anchor_mode", "sector")).strip().lower()
        if anchor_mode != "sm":
            try:
                validate_scenario_dict(bundle, data)
                return True, [], []
            except Exception as exc:
                return False, [str(exc)], []

        # Build allowed (sector, product) set from lists_sm or primary_map
        allowed_pairs: set[Tuple[str, str]] = set()
        scenario_lists_sm = data.get("lists_sm")
        if isinstance(scenario_lists_sm, list):
            for entry in scenario_lists_sm:
                if isinstance(entry, dict):
                    s = str(entry.get("Sector", "")).strip()
                    m = str(entry.get("Material", "")).strip()
                    if s and m:
                        allowed_pairs.add((s, m))
        if not allowed_pairs:
            pm = ((data.get("overrides") or {}).get("primary_map") or {})
            if isinstance(pm, dict):
                for s, entries in pm.items():
                    if isinstance(entries, list):
                        for e in entries:
                            if isinstance(e, dict):
                                prod = str(e.get("product", "")).strip()
                                if prod:
                                    allowed_pairs.add((str(s), prod))

        sectors_set = set(getattr(bundle.lists, "sectors", []))
        products_set = set(getattr(bundle.lists, "products", []))
        sm_param_prefixes = {
            "anchor_start_year",
            "anchor_client_activation_delay",
            "anchor_lead_generation_rate",
            "lead_to_pc_conversion_rate",
            "project_generation_rate",
            "max_projects_per_pc",
            "project_duration",
            "projects_to_client_conversion",
            "initial_phase_duration",
            "ramp_phase_duration",
            "ATAM",
            "initial_requirement_rate",
            "initial_req_growth",
            "ramp_requirement_rate",
            "ramp_req_growth",
            "steady_requirement_rate",
            "steady_req_growth",
            "requirement_to_order_lag",
            "requirement_limit_multiplier",
            "ramp_requirement_rate_override",
            "steady_requirement_rate_override",
        }

        def parse_sp(name: str) -> Tuple[bool, Tuple[str, str]]:
            for prefix in sm_param_prefixes:
                token = prefix + "_"
                if name.startswith(token):
                    suffix = name[len(token):]
                    parts = suffix.split("_")
                    if len(parts) >= 2:
                        sector = parts[0]
                        product = "_".join(parts[1:])
                        if sector in sectors_set and product in products_set:
                            return True, (sector, product)
            return False, ("", "")

        filtered = dict(data)
        overrides = dict((data.get("overrides") or {}))
        consts = dict((overrides.get("constants") or {}))
        for k in list(consts.keys()):
            is_sp, pair = parse_sp(k)
            if is_sp and pair not in allowed_pairs:
                orphan_constants.append(k)
                consts.pop(k, None)
        overrides["constants"] = consts
        filtered["overrides"] = overrides

        try:
            validate_scenario_dict(bundle, filtered)
            return True, [], orphan_constants
        except Exception as exc:
            return False, [str(exc)], orphan_constants

    def get_permissible_override_keys(self, anchor_mode: str = "sector") -> Dict[str, List[str]]:
        """Expose backend permissible keys for UI assistance.

        Uses the current inputs bundle and the provided anchor_mode to
        compute the permissible constants and points names.
        """
        bundle = load_phase1_inputs()
        result = list_permissible_override_keys(bundle, anchor_mode=anchor_mode)
        # Convert sets to sorted lists for UI friendliness
        return {
            "constants": sorted(result.get("constants", [])),
            "points": sorted(result.get("points", [])),
        }

    def get_lists_summary(self) -> Dict:
        """Return a small lists summary from backend for UI.

        Useful for building drop-downs; intentionally light.
        """
        bundle = load_phase1_inputs()
        return summarize_lists(bundle)

    def get_inputs_bundle(self):
        """Return the current Phase 1 inputs bundle (for UI state hydration)."""
        return load_phase1_inputs()

    # --- UI persistence helpers ---
    def _last_selected_path(self) -> Path:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        return LOGS_DIR / "ui_last_selection.json"

    def set_last_selected(self, name: str, anchor_mode: str) -> None:
        """Persist the last selected scenario and mode for UI reloads."""
        try:
            payload = {"name": str(name), "anchor_mode": str(anchor_mode)}
            with self._last_selected_path().open("w", encoding="utf-8") as f:
                json.dump(payload, f)
        except Exception:
            # best-effort persistence; ignore failures
            pass

    def get_last_selected(self) -> dict:
        """Return {name, anchor_mode} for last selection if available."""
        try:
            p = self._last_selected_path()
            if p.exists():
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {"name": str(data.get("name") or ""), "anchor_mode": str(data.get("anchor_mode") or "sector")}
        except Exception:
            pass
        return {"name": "", "anchor_mode": "sector"}


