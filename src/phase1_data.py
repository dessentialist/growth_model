from __future__ import annotations

"""
Phase 1 — Data Ingestion & Validation utilities (JSON-first).

Responsibilities:
- Load consolidated `inputs.json` at the project root
- Parse JSON into canonical DataFrames preserving legacy shapes:
  - `AnchorParams.by_sector`: parameters × sectors (wide)
  - `OtherParams.by_material`: parameters × materials (wide)
  - `ProductionTable.long`: [Year, Material, Capacity] (long)
  - `PricingTable.long`: [Year, Material, Price] (long)
  - `PrimaryMaterialMap.long`: [Sector, Material, StartYear] (long)
- Reconstruct a `ListsData` DataFrame of Market/Sector/Material combinations.

Design choices:
- No silent defaults; bad or missing inputs raise actionable errors
- US-only scope for now: we reconstruct lists under the "US" market
  and add TODOs for future EU/other market filtering expansions.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING

import json
import logging
import pandas as pd

if TYPE_CHECKING:  # avoid circular import at runtime
    from .scenario_loader import Scenario  # noqa: F401

# Module logger for structured diagnostics during ingestion
log = logging.getLogger(__name__)


# Note: CSV-specific helpers and loaders have been removed as we now ingest
# all inputs exclusively from `inputs.json`.


@dataclass
class ListsData:
    markets_sectors_materials: pd.DataFrame  # columns: Market, Sector, Material

    @property
    def sectors(self) -> List[str]:
        # Expose canonical sector names discovered from JSON `lists` reconstruction.
        # Note: these are used to build SD elements and scenario override keys,
        # so we preserve exact case and spacing from inputs.
        return self.markets_sectors_materials["Sector"].dropna().astype(str).str.strip().unique().tolist()

    @property
    def materials(self) -> List[str]:
        # Expose canonical material names discovered from JSON `lists` reconstruction.
        # These names must match other tables (other_params, production, pricing)
        # for coverage validation to pass.
        return self.markets_sectors_materials["Material"].dropna().astype(str).str.strip().unique().tolist()


@dataclass
class AnchorParams:
    # wide format: Parameter as index, columns are sectors
    by_sector: pd.DataFrame


@dataclass
class OtherParams:
    # wide format: Parameters as index, columns are materials
    by_material: pd.DataFrame


@dataclass
class ProductionTable:
    # long format: columns [Year, Material, Capacity]
    long: pd.DataFrame


@dataclass
class PricingTable:
    # long format: columns [Year, Material, Price]
    long: pd.DataFrame


@dataclass
class PrimaryMaterialMap:
    sector_to_materials: Dict[str, List[str]]
    long: pd.DataFrame


def parse_json_to_bundle(data: dict) -> "Phase1Bundle":
    """Construct a Phase1Bundle from the consolidated JSON structure.

    This parser preserves the original bundle's DataFrame shapes to avoid
    downstream breakage in model-building and tests.
    """
    # ----- Lists (US-only reconstruction per current scope) -----
    lists_section = data.get("lists", [])
    markets = []
    sectors = []
    materials = []
    if len(lists_section) >= 1:
        markets = list(lists_section[0].get("Market", []))
    if len(lists_section) >= 2:
        sectors = list(lists_section[1].get("Sector", []))
    if len(lists_section) >= 3:
        materials = list(lists_section[2].get("Material", []))

    # Filter to US; warn if absent
    if "US" not in markets:
        log.warning("No 'US' market found in lists; proceeding with empty 'US' reconstruction")
    target_market = "US"
    # TODO: Future EU expansion – support per-market filtering and rebuild lists accordingly
    rows_l = [{"Market": target_market, "Sector": s, "Material": m} for s in sectors for m in materials]
    lists_df = (
        pd.DataFrame(rows_l, columns=["Market", "Sector", "Material"])
        if rows_l
        else pd.DataFrame(columns=["Market", "Sector", "Material"])
    )
    lists = ListsData(lists_df)

    log.debug(
        "Parsed lists from JSON: markets=%s sectors=%d materials=%d rows=%d",
        markets,
        len(sectors),
        len(materials),
        len(lists_df),
    )

    # ----- Anchor parameters (params × sectors, numeric) -----
    # Build a wide DataFrame: index are parameter names; columns are sector labels.
    # All values are coerced to float without inserting defaults.
    anchor_dict: dict = data.get("anchor_params", {})
    anchor_params = sorted(anchor_dict.keys())
    all_sectors = sorted({s for p in anchor_params for s in anchor_dict.get(p, {}).keys()})
    anchor_df = pd.DataFrame(index=anchor_params, columns=all_sectors, dtype=float)
    for p in anchor_params:
        for s, v in anchor_dict.get(p, {}).items():
            try:
                anchor_df.at[p, s] = float(v)
            except Exception as exc:
                raise ValueError(f"Non-numeric value for anchor_params['{p}']['{s}'] = {v}") from exc
    anchor = AnchorParams(anchor_df)
    log.debug("Anchor params parsed: params=%d sectors=%d", len(anchor_params), len(all_sectors))

    # ----- Other parameters (params × materials, numeric) -----
    # Build a wide DataFrame: index are parameter names; columns are materials.
    other_dict: dict = data.get("other_params", {})
    other_params = sorted(other_dict.keys())
    all_materials = sorted({m for p in other_params for m in other_dict.get(p, {}).keys()})
    other_df = pd.DataFrame(index=other_params, columns=all_materials, dtype=float)
    for p in other_params:
        for m, v in other_dict.get(p, {}).items():
            try:
                other_df.at[p, m] = float(v)
            except Exception as exc:
                raise ValueError(f"Non-numeric value for other_params['{p}']['{m}'] = {v}") from exc
    other = OtherParams(other_df)
    log.debug("Other params parsed: params=%d materials=%d", len(other_params), len(all_materials))

    # ----- Production (long Year/Material/Capacity) -----
    # Expand dict-of-list entries into a long DataFrame. We intentionally keep
    # material names as-is (no normalization) to preserve alignment across
    # modules and with scenario naming.
    prod_dict: dict = data.get("production", {})
    prod_rows: List[dict] = []
    for mat, entries in prod_dict.items():
        # Keep material naming consistent with lists/other_params (no normalization here)
        normalized_mat = str(mat)
        for e in entries or []:
            try:
                prod_rows.append(
                    {
                        "Year": float(e["year"]),
                        "Material": normalized_mat,
                        "Capacity": float(e["capacity"]),
                    }
                )
            except Exception as exc:
                raise ValueError(f"Invalid production entry for material '{mat}': {e}") from exc
    prod_long = (
        pd.DataFrame(prod_rows, columns=["Year", "Material", "Capacity"])
        .sort_values(["Material", "Year"])
        .reset_index(drop=True)
        if prod_rows
        else pd.DataFrame(columns=["Year", "Material", "Capacity"])
    )
    production = ProductionTable(prod_long)
    log.debug("Production table rows: %d", len(prod_long))

    # ----- Pricing (long Year/Material/Price) -----
    # Analogous to production; entries are validated as floats and sorted.
    price_dict: dict = data.get("pricing", {})
    price_rows: List[dict] = []
    for mat, entries in price_dict.items():
        # Keep material naming consistent with lists/other_params (no normalization here)
        normalized_mat = str(mat)
        for e in entries or []:
            try:
                price_rows.append(
                    {
                        "Year": float(e["year"]),
                        "Material": normalized_mat,
                        "Price": float(e["price"]),
                    }
                )
            except Exception as exc:
                raise ValueError(f"Invalid pricing entry for material '{mat}': {e}") from exc
    price_long = (
        pd.DataFrame(price_rows, columns=["Year", "Material", "Price"])
        .sort_values(["Material", "Year"])
        .reset_index(drop=True)
        if price_rows
        else pd.DataFrame(columns=["Year", "Material", "Price"])
    )
    pricing = PricingTable(price_long)
    log.debug("Pricing table rows: %d", len(price_long))

    # ----- Primary material mapping -----
    # Build both a mapping (sector -> [materials]) and a long table for
    # convenience. StartYear <= 0 is allowed here; validation will warn.
    prim_dict: dict = data.get("primary_map", {})
    mapping: Dict[str, List[str]] = {}
    prim_rows: List[dict] = []
    for sector, entries in prim_dict.items():
        mats: List[str] = []
        for e in entries or []:
            # Keep material naming consistent with lists/other_params (no normalization here)
            mat = str(e.get("material", ""))
            try:
                start_year = float(e["start_year"])  # 0 allowed; later phases may warn
            except Exception as exc:
                raise ValueError(f"Invalid start_year for sector '{sector}' entry {e}") from exc
            mats.append(mat)
            prim_rows.append({"Sector": sector, "Material": mat, "StartYear": start_year})
        if mats:
            mapping[sector] = sorted(set(mats))
        else:
            mapping.setdefault(sector, [])
    prim_long = (
        pd.DataFrame(prim_rows, columns=["Sector", "Material", "StartYear"]).reset_index(drop=True)
        if prim_rows
        else pd.DataFrame(columns=["Sector", "Material", "StartYear"])
    )
    primary_map = PrimaryMaterialMap(mapping, prim_long)
    log.debug("Primary map: sectors=%d rows=%d", len(mapping.keys()), len(prim_long))

    # ----- Phase 16: Anchor per-(sector, material) parameters and lists_sm -----
    # Optional explicit SM list
    lists_sm_rows: List[dict] = []
    lists_sm_section = data.get("lists_sm") or []
    if isinstance(lists_sm_section, list):
        for e in lists_sm_section:
            try:
                s = str(e["Sector"]).strip()
                m = str(e["Material"]).strip()
                lists_sm_rows.append({"Sector": s, "Material": m})
            except Exception as exc:
                raise ValueError(f"Invalid lists_sm entry: {e}") from exc
    lists_sm_df = (
        pd.DataFrame(lists_sm_rows, columns=["Sector", "Material"]).drop_duplicates().reset_index(drop=True)
        if lists_sm_rows
        else pd.DataFrame(columns=["Sector", "Material"])
    )
    lists_sm_explicit = bool(lists_sm_rows)

    # If lists_sm is absent/empty, derive from primary_map as initial universe (best-guess)
    if lists_sm_df.empty and not prim_long.empty:
        lists_sm_df = prim_long[["Sector", "Material"]].drop_duplicates().reset_index(drop=True)
        # Derived from primary_map; mark as not explicit
        lists_sm_explicit = False

    # Anchor per-(s,m) parameters (Phase 16)
    anchor_params_sm_section = data.get("anchor_params_sm") or {}
    # Normalize into long table with columns [Sector, Material, Param, Value]
    anchor_sm_rows: List[dict] = []
    if isinstance(anchor_params_sm_section, dict):
        for param, by_sector in anchor_params_sm_section.items():
            if not isinstance(by_sector, dict):
                raise ValueError(f"anchor_params_sm['{param}'] must be a mapping sector -> material -> value")
            for sector, by_material in by_sector.items():
                if not isinstance(by_material, dict):
                    raise ValueError(f"anchor_params_sm['{param}']['{sector}'] must be a mapping material -> value")
                for material, value in by_material.items():
                    try:
                        anchor_sm_rows.append(
                            {
                                "Sector": str(sector),
                                "Material": str(material),
                                "Param": str(param),
                                "Value": float(value),
                            }
                        )
                    except Exception as exc:
                        raise ValueError(
                            f"Non-numeric value for anchor_params_sm['{param}']['{sector}']['{material}'] = {value}"
                        ) from exc
    anchor_sm_long = (
        pd.DataFrame(anchor_sm_rows, columns=["Sector", "Material", "Param", "Value"]).reset_index(drop=True)
        if anchor_sm_rows
        else pd.DataFrame(columns=["Sector", "Material", "Param", "Value"])
    )

    # Final assembly of the bundle. Types satisfy downstream model building
    # and scenario validation without requiring reformatting.
    try:
        bundle = Phase1Bundle(  # type: ignore[call-arg]
            lists=lists,
            anchor=anchor,
            other=other,
            production=production,
            pricing=pricing,
            primary_map=primary_map,
            anchor_sm=anchor_sm_long,
            lists_sm=lists_sm_df,
            lists_sm_explicit=lists_sm_explicit,
        )
    except TypeError:
        bundle = Phase1Bundle(  # type: ignore[misc]
            lists=lists, anchor=anchor, other=other, 
            production=production, pricing=pricing
        )
    return bundle

    # CSV loader functions have been removed.


def validate_coverage(bundle: Phase1Bundle) -> None:
    """Validate structural coverage and basic invariants for Phase 1 inputs.

    Checks performed (Phase 3 enhancements included):
    - US-only market enforcement: reconstructed lists must include 'US'.
    - Anchor params cover all listed sectors; Other params cover all listed materials.
    - Production/Pricing tables contain rows for each listed material with
      strictly increasing Year and non-negative values.
    - Primary material mapping sectors/materials are known; warn when
      StartYear <= 0 (treated as disabled/placeholder).
    """
    sectors = set(bundle.lists.sectors)
    materials = set(bundle.lists.materials)

    # US-only enforcement for Phase 1 lists reconstruction
    markets_present = set(bundle.lists.markets_sectors_materials.get("Market", []).unique())
    if "US" not in markets_present:
        raise ValueError("No 'US' market in reconstructed lists — Phase 1 assumes US-only scope")

    # Anchor params: index are parameter names; columns are sector names
    missing_sectors = sectors.difference(set(bundle.anchor.by_sector.columns))
    if missing_sectors:
        raise ValueError(f"Anchor parameters missing sectors: {sorted(missing_sectors)}")

    # Other params: columns are material names
    missing_materials = materials.difference(set(bundle.other.by_material.columns))
    if missing_materials:
        raise ValueError(f"Other client parameters missing materials: {sorted(missing_materials)}")

    # Production & pricing tables should include every material with at least one row
    prod_mats = set(bundle.production.long["Material"].unique())
    price_mats = set(bundle.pricing.long["Material"].unique())
    if not materials.issubset(prod_mats):
        raise ValueError(f"Production table missing materials: {sorted(materials.difference(prod_mats))}")
    if not materials.issubset(price_mats):
        raise ValueError(f"Pricing table missing materials: {sorted(materials.difference(price_mats))}")

    # Time strictly increasing per material for production and pricing
    for name, long_df, val_col in (
        ("Production", bundle.production.long, "Capacity"),
        ("Pricing", bundle.pricing.long, "Price"),
    ):
        for material, g in long_df.groupby("Material"):
            if (g["Year"].diff().fillna(1) <= 0).any():
                raise ValueError(f"{name} table non-increasing years for material '{material}'")
            if (g[val_col] < 0).any():
                raise ValueError(f"{name} table has negative {val_col.lower()} for material '{material}'")

    # Primary material mapping consistency
    mapped_sectors = set(bundle.primary_map.sector_to_materials.keys())
    if not mapped_sectors.issubset(sectors):
        raise ValueError(f"Primary Material mapping has unknown sectors: {sorted(mapped_sectors.difference(sectors))}")
    mapped_materials = set(bundle.primary_map.long["Material"].unique())
    if not mapped_materials.issubset(materials):
        raise ValueError(f"Primary Material mapping has unknown materials: {sorted(mapped_materials.difference(materials))}")

    # Warn on disabled/placeholder start years (<= 0) in primary material mapping
    if not bundle.primary_map.long.empty:
        disabled_rows = bundle.primary_map.long[bundle.primary_map.long["StartYear"] <= 0]
        if not disabled_rows.empty:
            # Log a concise list of sector-material pairs with non-positive start years
            pairs = [f"{row['Sector']}→{row['Material']}" for _, row in disabled_rows.iterrows()]
            log.warning(
                "Primary material mapping contains non-positive StartYear for: %s",
                ", ".join(pairs),
            )

    # Phase 16 validations: lists_sm and anchor_sm coverage
    # Build SM universe
    sm_df = getattr(bundle, "lists_sm", pd.DataFrame(columns=["Sector", "Material"]))
    if sm_df is not None and not sm_df.empty:
        # Ensure all (s,m) exist in lists and mapping tables
        unknown_s = set(sm_df["Sector"]) - sectors
        unknown_m = set(sm_df["Material"]) - materials
        if unknown_s:
            raise ValueError(f"lists_sm contains unknown sectors: {sorted(unknown_s)}")
        if unknown_m:
            raise ValueError(f"lists_sm contains unknown materials: {sorted(unknown_m)}")
    # Validate anchor_sm Param/Value are present for targeted params when provided
    anchor_sm_df = getattr(bundle, "anchor_sm", pd.DataFrame(columns=["Sector", "Material", "Param", "Value"]))
    if anchor_sm_df is not None and not anchor_sm_df.empty:
        # required columns present
        for col in ("Sector", "Material", "Param", "Value"):
            if col not in anchor_sm_df.columns:
                raise ValueError(f"anchor_sm missing column '{col}'")
        # check references exist
        ref_unknown_s = set(anchor_sm_df["Sector"]) - sectors
        ref_unknown_m = set(anchor_sm_df["Material"]) - materials
        if ref_unknown_s:
            raise ValueError(f"anchor_sm contains unknown sectors: {sorted(ref_unknown_s)}")
        if ref_unknown_m:
            raise ValueError(f"anchor_sm contains unknown materials: {sorted(ref_unknown_m)}")


# Primary material mapping is parsed from JSON; CSV mapping loader has been removed.


@dataclass
class Phase1Bundle:
    """Container for all Phase 1 inputs constructed from JSON.

    Keeping types and shapes stable preserves downstream expectations in the
    model, naming, and scenario modules.
    """

    lists: ListsData
    anchor: AnchorParams
    other: OtherParams
    production: ProductionTable
    pricing: PricingTable
    primary_map: PrimaryMaterialMap
    # Phase 16 additions
    anchor_sm: pd.DataFrame | None = None  # columns [Sector, Material, Param, Value]
    lists_sm: pd.DataFrame | None = None  # columns [Sector, Material]
    # Phase 17.1: Track whether lists_sm was explicitly provided (True) or
    # derived from primary_map as a best-guess (False). SM-mode requires an
    # explicit lists_sm in inputs.json and must not rely on derivation.
    lists_sm_explicit: bool = False


def load_phase1_inputs(json_path: Path = Path("inputs.json")) -> Phase1Bundle:
    """Load Phase 1 inputs exclusively from the consolidated JSON file.

    Parameters
    ----------
    json_path : Path
        Absolute or relative path to the `inputs.json` file (defaults to
        project root).
    """
    # Allow callers to pass either a file path or a directory (e.g., legacy
    # usages passing `Path("Inputs")`).
    #
    # Important: We are JSON-only by design (no CSV fallbacks). If a directory
    # is provided, we attempt to resolve `inputs.json` inside it. If that file
    # is not present, we fall back to the project-root `inputs.json`. This keeps
    # the call sites simple (tests may continue to pass `Path("Inputs")`) while
    # preserving the mandate to read exclusively from JSON.
    target_path: Path = json_path
    if target_path.is_dir():
        candidate = target_path / "inputs.json"
        target_path = candidate if candidate.exists() else Path("inputs.json")

    log.info("Loading Phase 1 inputs from JSON: %s", target_path)
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise ValueError(f"inputs.json not found at {target_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Malformed JSON in inputs.json") from exc

    # Phase 3 validation: root structure must include 'lists'
    if not isinstance(data, dict) or "lists" not in data:
        raise ValueError("Missing 'lists' key in inputs.json")

    bundle = parse_json_to_bundle(data)
    # Validate to catch structural issues early
    validate_coverage(bundle)
    return bundle


def apply_primary_map_overrides(bundle: Phase1Bundle, scenario: "Scenario" | None) -> Phase1Bundle:
    """Phase 13: merge scenario-provided primary_map overrides into the bundle.

    - When present, overrides replace the sector's material list entirely with the provided list
      (no partial merges to avoid ambiguity). Sectors not present remain unchanged.
    - Validates presence via `validate_coverage` after merge.
    """
    if scenario is None or not getattr(scenario, "primary_map", None):
        return bundle

    pm_override = scenario.primary_map or {}

    # Build new mapping dict merging overrides (replace per sector)
    new_mapping: Dict[str, List[str]] = dict(bundle.primary_map.sector_to_materials)
    for sector, entries in pm_override.items():
        # entries are list of (material, start_year)
        new_mapping[sector] = [m for (m, _sy) in entries]

    # Build new long table by replacing rows for overridden sectors
    keep_rows = bundle.primary_map.long[~bundle.primary_map.long["Sector"].isin(pm_override.keys())]
    new_rows = []
    for sector, entries in pm_override.items():
        for m, sy in entries:
            new_rows.append({"Sector": sector, "Material": m, "StartYear": float(sy)})
    import pandas as pd

    merged_long = pd.concat(
        [keep_rows, pd.DataFrame(new_rows, columns=["Sector", "Material", "StartYear"])], ignore_index=True
    ).reset_index(drop=True)

    new_pm = PrimaryMaterialMap(new_mapping, merged_long)
    # Preserve SM-mode structures (anchor_sm, lists_sm, explicitness flag)
    merged_bundle = Phase1Bundle(
        lists=bundle.lists,
        anchor=bundle.anchor,
        other=bundle.other,
        production=bundle.production,
        pricing=bundle.pricing,
        primary_map=new_pm,
        anchor_sm=getattr(bundle, "anchor_sm", None),
        lists_sm=getattr(bundle, "lists_sm", None),
        lists_sm_explicit=getattr(bundle, "lists_sm_explicit", False),
    )
    # Validate merged bundle
    validate_coverage(merged_bundle)
    return merged_bundle


def merge_scenario_sm_constants_into_bundle(bundle: Phase1Bundle, scenario: "Scenario") -> Phase1Bundle:
    """Lift scenario per-(sector, material) constants into bundle.anchor_sm for SM-mode build.

    This enables scenarios to define missing per-(s,m) values that are required by SM-mode,
    so that the SD model can create constants at build time.
    """
    from .naming import anchor_constant_sm
    import pandas as pd

    if scenario is None or not getattr(scenario, "constants", None):
        return bundle

    targeted_params = {
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
    }

    sm_df_universe = getattr(bundle, "lists_sm", None)
    if sm_df_universe is None or sm_df_universe.empty:
        sm_df_universe = bundle.primary_map.long[["Sector", "Material"]].drop_duplicates()

    rows: list[dict] = []
    for _, sm in sm_df_universe.iterrows():
        s = str(sm["Sector"]).strip()
        m = str(sm["Material"]).strip()
        for p in targeted_params:
            key = anchor_constant_sm(p, s, m)
            if key in scenario.constants:
                try:
                    val = float(scenario.constants[key])
                except Exception:
                    continue
                rows.append({"Sector": s, "Material": m, "Param": p, "Value": val})

    if not rows:
        return bundle

    add = pd.DataFrame(rows, columns=["Sector", "Material", "Param", "Value"])
    current = getattr(bundle, "anchor_sm", None)
    if current is None or current.empty:
        merged = add
    else:
        merged = (
            pd.concat([current, add], ignore_index=True)
            .drop_duplicates(subset=["Sector", "Material", "Param"], keep="last")
            .reset_index(drop=True)
        )

    return Phase1Bundle(
        lists=bundle.lists,
        anchor=bundle.anchor,
        other=bundle.other,
        production=bundle.production,
        pricing=bundle.pricing,
        primary_map=bundle.primary_map,
        anchor_sm=merged,
        lists_sm=bundle.lists_sm,
        lists_sm_explicit=bundle.lists_sm_explicit,
    )


def apply_lists_sm_override(bundle: Phase1Bundle, scenario: "Scenario" | None) -> Phase1Bundle:
    """Apply scenario-provided lists_sm (SM universe) to the Phase1 bundle.

    - When `scenario.lists_sm` is provided, it takes precedence over `inputs.json` lists_sm
      for this run. We construct a DataFrame with columns [Sector, Material], drop duplicates,
      validate references against `lists`, and mark `lists_sm_explicit = True`.
    - Otherwise, return the bundle unchanged.
    """
    if scenario is None or not getattr(scenario, "lists_sm", None):
        return bundle

    import pandas as pd

    pairs = list(getattr(scenario, "lists_sm"))  # type: ignore[arg-type]
    df = pd.DataFrame(pairs, columns=["Sector", "Material"]).drop_duplicates().reset_index(drop=True)

    # Validate references exist in lists
    sectors = set(bundle.lists.sectors)
    materials = set(bundle.lists.materials)
    unknown_s = set(df["Sector"]) - sectors
    unknown_m = set(df["Material"]) - materials
    if unknown_s:
        raise ValueError(f"scenario.lists_sm contains unknown sectors: {sorted(unknown_s)}")
    if unknown_m:
        raise ValueError(f"scenario.lists_sm contains unknown materials: {sorted(unknown_m)}")

    return Phase1Bundle(
        lists=bundle.lists,
        anchor=bundle.anchor,
        other=bundle.other,
        production=bundle.production,
        pricing=bundle.pricing,
        primary_map=bundle.primary_map,
        anchor_sm=getattr(bundle, "anchor_sm", None),
        lists_sm=df,
        lists_sm_explicit=True,
    )
