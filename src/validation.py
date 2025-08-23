from __future__ import annotations

"""
Phase 9 — Logging, Validation, and Error Policy utilities.

This module centralizes scenario echoing and runtime validation checks used by the
stepwise runner. The goal is to keep the runner concise while ensuring that all
Phase 9 success criteria are enforced:

- Scenario echo of applied overrides to logs and console
- Step-level sampling of gateway inputs and core signals (optional, DEBUG)
- Validation checks each step:
  * Fulfillment ratio ∈ [0, 1]
  * Agents-To-Create signals are non-negative integers
  * Per-step revenue identity holds within a tight tolerance

All functions raise a ValueError/RuntimeError with actionable messages when a
validation fails, so the runner can stop early and print a snapshot.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

from .naming import (
    agent_demand_sector_input,
    anchor_delivery_flow_product,
    anchor_delivery_flow_sector_product,
    agents_to_create_converter,
    agents_to_create_converter_sm,
    fulfillment_ratio,
    price_converter_product,
)
from .scenario_loader import Scenario


def echo_scenario_overrides(*, log_dir: Path, scenario: Scenario, log: logging.Logger) -> Path:
    """Write a human-readable echo of scenario configuration and applied overrides to logs.

    Two files are written for convenience:
    - scenario_overrides_echo.json
    - scenario_overrides_echo.yaml (JSON but .yaml extension for easy viewing)

    Phase 17.7: Include SM-mode runspecs (anchor_mode) and seeds blocks for traceability.

    The function also logs summary counts and a few example keys.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    echo = {
        "name": scenario.name,
        "runspecs": {
            "starttime": float(scenario.runspecs.starttime),
            "stoptime": float(scenario.runspecs.stoptime),
            "dt": float(scenario.runspecs.dt),
            "anchor_mode": str(getattr(scenario.runspecs, "anchor_mode", "sector")),
        },
        "overrides": {
            "constants": {k: float(v) for k, v in sorted(scenario.constants.items())},
            "points": {k: [(float(t), float(v)) for (t, v) in v] for k, v in sorted(scenario.points.items())},
        },
        "seeds": {
            # Present only if provided in scenario (omit empty dicts for readability)
            "active_anchor_clients": dict(getattr(scenario, "seeds_active_anchor_clients", {}) or {}),
            "elapsed_quarters": dict(getattr(scenario, "seeds_elapsed_quarters", {}) or {}),
            "direct_clients": dict(getattr(scenario, "seeds_direct_clients", {}) or {}),
            "active_anchor_clients_sm": dict(getattr(scenario, "seeds_active_anchor_clients_sm", {}) or {}),
        },
    }

    json_path = log_dir / "scenario_overrides_echo.json"
    yaml_path = log_dir / "scenario_overrides_echo.yaml"
    json_path.write_text(json.dumps(echo, indent=2), encoding="utf-8")
    # Keep format consistent to avoid YAML dependency; JSON is valid YAML
    yaml_path.write_text(json.dumps(echo, indent=2), encoding="utf-8")

    log.info(
        "Scenario overrides applied: %d constants, %d lookups",
        len(scenario.constants),
        len(scenario.points),
    )
    if scenario.constants:
        sample_keys = list(sorted(scenario.constants.keys()))[:5]
        log.debug("Override constants (sample): %s", sample_keys)
    if scenario.points:
        sample_keys = list(sorted(scenario.points.keys()))[:5]
        log.debug("Override lookups (sample): %s", sample_keys)

    return json_path


def validate_agents_to_create_signals(
    *, model, sectors: Iterable[str], t: float, log: Optional[logging.Logger] = None
) -> None:
    """Ensure `Agents_To_Create_<sector>` are non-negative integers at time t.

    - Raises RuntimeError if any sector has a negative or non-integer value.
    """
    for sector in sectors:
        name = agents_to_create_converter(sector)
        val = float(model.evaluate_equation(name, t))
        # Non-negativity
        if val < -1e-9:
            msg = f"Validation failed at t={t:.2f}: {name} negative ({val})"
            if log:
                log.error(msg)
            raise RuntimeError(msg)
        # Integer-ness within tight tolerance
        if abs(val - round(val)) > 1e-9:
            msg = f"Validation failed at t={t:.2f}: {name} not an integer ({val})"
            if log:
                log.error(msg)
            raise RuntimeError(msg)


def validate_agents_to_create_sm_signals(
    *, model, pairs: Iterable[tuple[str, str]], t: float, log: Optional[logging.Logger] = None
) -> None:
    """Ensure `Agents_To_Create_<sector>_<product>` are non-negative integers at time t.

    Parameters
    ----------
    model : BPTK_Py Model-like
        The compiled SD model instance with converters
    pairs : Iterable[tuple[str, str]]
        Iterable of (sector, product) pairs to validate
    t : float
        Current absolute time in years
    log : Optional[logging.Logger]
        Logger for emitting error messages prior to raising
    """
    for sector, product in pairs:
        name = agents_to_create_converter_sm(sector, product)
        val = float(model.evaluate_equation(name, t))
        if val < -1e-9:
            msg = f"Validation failed at t={t:.2f}: {name} negative ({val})"
            if log:
                log.error(msg)
            raise RuntimeError(msg)
        if abs(val - round(val)) > 1e-9:
            msg = f"Validation failed at t={t:.2f}: {name} not an integer ({val})"
            if log:
                log.error(msg)
            raise RuntimeError(msg)


def validate_fulfillment_ratio_bounds(
    *, model, products: Iterable[str], t: float, log: Optional[logging.Logger] = None
) -> None:
    """Ensure `Fulfillment_Ratio_<p>` ∈ [0, 1] for all products at time t.

    This protects against mis-wiring in equations where capacity or total demand
    could produce a ratio outside the expected bounds.
    """
    for m in products:
        name = fulfillment_ratio(m)
        val = float(model.evaluate_equation(name, t))
        if not (0.0 - 1e-12 <= val <= 1.0 + 1e-12):
            msg = f"Fulfillment ratio out of bounds at t={t:.2f} for {name}: {val}"
            if log:
                log.error(msg)
            raise RuntimeError(msg)


def validate_revenue_identity(
    *, model, products: Iterable[str], product_to_sectors: Mapping[str, List[str]], t: float
) -> None:
    """Validate per-step revenue identity:

    Sum over products of (sum_s Anchor_Delivery_Flow_{s,p} * Price_p) + (Client_Delivery_Flow_p * Price_p)
    equals sum over products of ((Anchor_Delivery_Flow_p + Client_Delivery_Flow_p) * Price_p)
    within a tight floating-point tolerance.
    """
    anchor_total = 0.0
    client_total = 0.0
    combined_total = 0.0
    for m in products:
        price = float(model.evaluate_equation(price_converter_product(m), t))
        adf_m = float(model.evaluate_equation(anchor_delivery_flow_product(m), t))
        # Client side is named in caller; avoid import cycle by evaluating by name
        cdf = float(model.evaluate_equation(f"Client_Delivery_Flow_{m.replace(' ', '_')}", t))

        # Anchor by sector for accumulation
        sectors = product_to_sectors.get(m, [])
        for s in sectors:
            adf_sm = float(model.evaluate_equation(anchor_delivery_flow_sector_product(s, m), t))
            anchor_total += adf_sm * price

        client_total += cdf * price
        combined_total += (adf_m + cdf) * price

    # Tolerance accounts for floating-point rounding in the DSL evaluation
    tol = 1e-8 * max(1.0, abs(combined_total))
    if abs((anchor_total + client_total) - combined_total) > tol:
        raise RuntimeError(
            "Revenue identity failed at t={t:.2f}: anchor+client={ac:.6f}, combined={ct:.6f}".format(
                t=t, ac=(anchor_total + client_total), ct=combined_total
            )
        )


def sample_gateways(
    *,
    model,
    sector_to_products: Mapping[str, List[str]],
    t: float,
    log: logging.Logger,
    sample_products: Optional[List[str]] = None,
) -> None:
    """DEBUG sampling: log sector–product gateway inputs and per-product sums.

    - If `sample_products` is None, uses the first product seen in the mapping.
    - Logs per-sector values and the aggregated total for each sampled product.
    """
    # Build product → sectors index from the provided mapping
    prod_to_secs: Dict[str, List[str]] = {}
    for sector, prods in sector_to_products.items():
        for p in prods:
            prod_to_secs.setdefault(p, []).append(sector)

    if not sample_products:
        sample_products = list(prod_to_secs.keys())[:1]

    for m in sample_products:
        sectors = prod_to_secs.get(m, [])
        parts: List[str] = []
        total = 0.0
        for s in sectors:
            name_sm = agent_demand_sector_input(s, m)
            v = float(model.evaluate_equation(name_sm, t))
            parts.append(f"{s}={v:.4f}")
            total += v
        log.debug("t=%.2f Gateway %s: %s | sum=%.4f", t, m, ", ".join(parts) if parts else "(none)", total)
