from __future__ import annotations

"""
Phase 8/15 — KPI Extraction & CSV Writer (variable horizon)

This module computes per-step KPI series from the hybrid SD+ABM model and
writes them to a deterministic CSV file `output/FFF_Growth_System_Complete_Results.csv`.

Design goals
- Keep extraction independent of internal model storage by using
  `model.evaluate_equation(name, t)` on canonical element names.
- Use runner-managed agent state to compute agent-based KPIs (Anchor Clients and
  Active Projects) without modifying the SD model.
- Phase 15: Emit exactly one column per simulated step based on `runspecs`
  (no fixed 28-quarter truncation/padding). Labels are derived from the time grid.
- Phase 17.6: Support optional per-(sector, material) diagnostic rows without
  changing the default KPI surface. Optional rows are appended to the standard
  ordering only when explicitly enabled by caller flags.

Inputs
- `model`: BPTK_Py SD model built by Phase 4/6 and used by the runner
- `bundle`: Phase 1 inputs (for sector/material lists and mappings)
- `run_grid`: start, dt, num_steps
- `agents_by_sector`: dict[sector] -> list[AnchorClientAgent] created by the runner

Outputs
- A mapping from row label to `num_steps` floats
- A CSV written to `output/FFF_Growth_System_Complete_Results.csv`
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping

import pandas as pd

from .io_paths import OUTPUT_DIR
from .naming import (
    # sector-level
    anchor_lead_generation,
    anchor_delivery_flow_sector_material,
    # material-level
    total_demand,
    client_delivery_flow,
    anchor_delivery_flow_material,
    price_converter,
    c_stock,
    total_new_leads,
)


@dataclass(frozen=True)
class RunGrid:
    start: float
    dt: float
    num_steps: int


def _quarter_labels_from_grid(start_year: float, dt_years: float, num_steps: int) -> List[str]:
    """Return labels `YYYYQn` for each step on the time grid.

    - Uses the absolute time per step: t_i = start_year + i*dt_years
    - Maps fractional year to nearest quarter: Q1=.00, Q2=.25, Q3=.50, Q4=.75
    - Works for arbitrary `dt_years` (not necessarily 0.25)
    """
    labels: List[str] = []
    for i in range(num_steps):
        t = start_year + dt_years * i
        year = int(t)
        frac = t - year
        # Map to nearest quarter index 0..3
        quarter_index = int(round(frac / 0.25)) % 4
        labels.append(f"{year}Q{quarter_index + 1}")
    return labels


def _init_series(rows: List[str]) -> Dict[str, List[float]]:
    """Initialize a dict of lists for the provided row labels."""
    return {r: [] for r in rows}


def _ensure_equal_length(series_map: Dict[str, List[float]], expected: int) -> None:
    """Ensure all series have exactly `expected` entries by padding/truncating.

    Phase 15: This is a safety check; normally we emit exactly `num_steps` values.
    """
    for key, values in series_map.items():
        if len(values) < expected:
            values.extend([0.0] * (expected - len(values)))
        elif len(values) > expected:
            del values[expected:]


def _safe_eval(model, name: str, t: float) -> float:
    """Evaluate an SD element at time `t`, returning float; missing → 0.0.

    Notes:
    - Production flow requires runner-captured KPIs; this helper exists solely
      for evaluating primitive SD elements during the run (e.g., lookups/flows)
      and is not a post-run fallback.
    """
    try:
        return float(model.evaluate_equation(name, t))
    except Exception:
        return 0.0


def collect_kpis_for_step(
    *,
    model,
    bundle,
    t: float,
    agents_by_sector: Mapping[str, List[object]],
    sector_to_materials: Mapping[str, List[str]],
    step_idx: int,
    agent_metrics_by_step: List[Mapping[str, object]],
) -> Dict[str, float]:
    """Compute all KPI values for a single step at absolute time `t`.

    Returns a flat mapping of row label → numeric value for the given step.
    """
    out: Dict[str, float] = {}

    sectors: List[str] = list(bundle.lists.sectors)
    materials: List[str] = list(bundle.lists.materials)

    # Validate availability of per-step ABM metrics for this step
    if (agent_metrics_by_step is None or not isinstance(step_idx, int) or 
            not (0 <= step_idx < len(agent_metrics_by_step))):
        raise RuntimeError(
            "Per-step ABM metrics are required: provide agent_metrics_by_step with length "
            "covering all emitted steps, and a valid step_idx."
        )

    # ----- Material-level base series -----
    for m in materials:
        td = _safe_eval(model, total_demand(m), t)
        cdf = _safe_eval(model, client_delivery_flow(m), t)
        adf_m = _safe_eval(model, anchor_delivery_flow_material(m), t)
        price = _safe_eval(model, price_converter(m), t)

        out[f"Order Basket {m}"] = td
        out[f"Order Delivery {m}"] = adf_m + cdf
        out[f"Revenue {m}"] = (adf_m + cdf) * price

        # Other Clients stock (cumulative clients by material)
        out[f"Other Clients {m}"] = _safe_eval(model, c_stock(m), t)

    # ----- Sector-level series -----
    for s in sectors:
        # Anchor Leads per sector reported as per-quarter units.
        # Model's converter is scaled to per-year for correct stock integration.
        # For per-quarter KPI, multiply by `dt` (years per step).
        # NOTE: The caller (runner) will prefer real-time captured values.
        # When using this function directly, set the correct dt-based scaling externally if needed.
        # We keep division-by-4 logic out here to avoid hardcoding a specific dt.
        # The runner's live capture will compute this correctly.
        out[f"Anchor Leads {s}"] = _safe_eval(model, anchor_lead_generation(s), t)

        # Anchor revenue per sector = sum_m Anchor_Delivery_Flow_<s>_<m> * Price_<m>
        sector_rev = 0.0
        for m in sector_to_materials.get(s, []):
            adf_sm = _safe_eval(model, anchor_delivery_flow_sector_material(s, m), t)
            price = _safe_eval(model, price_converter(m), t)
            sector_rev += adf_sm * price
        out[f"Revenue {s}"] = sector_rev

        # Anchor Clients and Active Projects per sector from runner-provided per-step metrics
        step_metrics = agent_metrics_by_step[step_idx]
        active_value = float(step_metrics.get("active_by_sector", {}).get(s, 0))
        inprog_value = float(step_metrics.get("inprogress_by_sector", {}).get(s, 0))
        out[f"Anchor Clients {s}"] = active_value
        out[f"Active Projects {s}"] = inprog_value

    # ----- Totals across dimensions -----
    # Revenue total = sum material-level revenue
    out["Revenue"] = sum(out.get(f"Revenue {m}", 0.0) for m in materials)

    # Anchor Leads total = sum sector-level per-quarter leads
    out["Anchor Leads"] = sum(out.get(f"Anchor Leads {s}", 0.0) for s in sectors)

    # Other Clients total = sum material-level C_<m> stocks
    out["Other Clients"] = sum(out.get(f"Other Clients {m}", 0.0) for m in materials)

    # Other Leads total only (do not map to sectors to avoid duplication).
    # Other clients are material-driven and not attributed to sectors. Revenue
    # by sector is anchor-only by design.
    # Other Leads should be expressed as per-quarter units in KPIs.
    # The underlying SD converters for inbound/outbound leads are scaled to per-year.
    # Per-quarter presentation should be handled by the caller using dt.
    other_leads_total = 0.0
    for m in materials:
        other_leads_total += _safe_eval(model, total_new_leads(m), t)
    out["Other Leads"] = other_leads_total

    # Order Basket total
    out["Order Basket"] = sum(out.get(f"Order Basket {m}", 0.0) for m in materials)
    # Order Delivery total
    out["Order Delivery"] = sum(out.get(f"Order Delivery {m}", 0.0) for m in materials)
    # Anchor Clients total and Active Projects total from per-step metrics
    step_metrics = agent_metrics_by_step[step_idx]
    out["Anchor Clients"] = float(step_metrics.get("active_total", 0.0))
    out["Active Projects"] = float(step_metrics.get("inprogress_total", 0.0))

    return out


def build_row_order(
    *,
    sectors: List[str],
    materials: List[str],
    include_sm_revenue_rows: bool = False,
    include_sm_client_rows: bool = False,
    sector_to_materials: Mapping[str, List[str]] | None = None,
) -> List[str]:
    """Return a deterministic row order matching the architecture template.

    Phase 17.6: Optionally append granular per-(sector, material) diagnostics
    without changing the default surface.
    """
    rows: List[str] = []
    # Revenue
    rows.append("Revenue")
    rows.extend([f"Revenue {s}" for s in sectors])
    rows.extend([f"Revenue {m}" for m in materials])
    # Optional: granular per-(s,m) revenue rows
    if include_sm_revenue_rows and sector_to_materials is not None:
        for s in sectors:
            for m in sector_to_materials.get(s, []):
                rows.append(f"Revenue {s} {m}")
    # Anchor Leads
    rows.append("Anchor Leads")
    rows.extend([f"Anchor Leads {s}" for s in sectors])
    # Active Projects
    rows.append("Active Projects")
    rows.extend([f"Active Projects {s}" for s in sectors])
    # Anchor Clients
    rows.append("Anchor Clients")
    rows.extend([f"Anchor Clients {s}" for s in sectors])
    # Optional: granular per-(s,m) anchor clients (primarily meaningful in SM-mode)
    if include_sm_client_rows and sector_to_materials is not None:
        for s in sectors:
            for m in sector_to_materials.get(s, []):
                rows.append(f"Anchor Clients {s} {m}")
    # Other Leads (total only; per-sector rows removed as Other Leads are material-mapped)
    rows.append("Other Leads")
    # Other Clients
    rows.append("Other Clients")
    rows.extend([f"Other Clients {m}" for m in materials])
    # Order Basket
    rows.append("Order Basket")
    rows.extend([f"Order Basket {m}" for m in materials])
    # Order Delivery
    rows.append("Order Delivery")
    rows.extend([f"Order Delivery {m}" for m in materials])
    return rows


def write_kpis_csv(
    *,
    series_by_row: Dict[str, List[float]],
    labels: List[str],
    output_dir: Path | None = None,
) -> Path:
    """Write the KPI series to CSV and return the file path.

    Columns: ["Output Stocks", labels...]. The order of rows follows the order
    of keys in `series_by_row`.
    """
    out_dir = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "FFF_Growth_System_Complete_Results.csv"

    # Build DataFrame in the provided order
    df = pd.DataFrame(
        {
            "Output Stocks": list(series_by_row.keys()),
            **{label: [series_by_row[row][idx] for row in series_by_row.keys()] for idx, label in enumerate(labels)},
        }
    )
    df.to_csv(out_path, index=False)
    return out_path


def extract_and_write_kpis(
    *,
    model,
    bundle,
    run_grid: RunGrid,
    agents_by_sector: Mapping[str, List[object]],
    sector_to_materials: Mapping[str, List[str]],
    output_dir: Path | None = None,
    agent_metrics_by_step: List[Mapping[str, object]] | None = None,
    kpi_values_by_step: List[Dict[str, float]] | None = None,
    include_sm_revenue_rows: bool = False,
    include_sm_client_rows: bool = False,
) -> Path:
    """End-to-end helper: compute KPI series for all simulated steps and write CSV.

    Strict policy: runner-captured KPI values are required.
    - `kpi_values_by_step` must be provided and contain one dict per emitted step.
    - This eliminates the post-run fallback evaluation path that could produce
      unit inconsistencies (e.g., per-year vs per-step for leads).

    `agent_metrics_by_step` is retained for interface compatibility but is not
    used here once historical KPI values are provided by the runner.
    """
    steps_to_emit = run_grid.num_steps

    sectors: List[str] = list(bundle.lists.sectors)
    materials: List[str] = list(bundle.lists.materials)
    ordered_rows: List[str] = build_row_order(
        sectors=sectors,
        materials=materials,
        include_sm_revenue_rows=include_sm_revenue_rows,
        include_sm_client_rows=include_sm_client_rows,
        sector_to_materials=sector_to_materials,
    )
    series = _init_series(ordered_rows)

    # Require runner-captured KPI values and validate length
    if kpi_values_by_step is None:
        raise ValueError("kpi_values_by_step is required; provide runner-captured per-step KPI values")
    if len(kpi_values_by_step) < steps_to_emit:
        raise ValueError(
            f"kpi_values_by_step length ({len(kpi_values_by_step)}) is less than required steps ({steps_to_emit})"
        )

    # Collect step values strictly from captured history
    for step_idx in range(steps_to_emit):
        step_vals = kpi_values_by_step[step_idx]
        for row in ordered_rows:
            series[row].append(float(step_vals.get(row, 0.0)))

    # Ensure consistent length
    _ensure_equal_length(series, steps_to_emit)
    labels = _quarter_labels_from_grid(run_grid.start, run_grid.dt, steps_to_emit)
    return write_kpis_csv(series_by_row=series, labels=labels, output_dir=output_dir)


__all__ = [
    "RunGrid",
    "collect_kpis_for_step",
    "build_row_order",
    "extract_and_write_kpis",
]
