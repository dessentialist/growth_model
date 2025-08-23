#!/usr/bin/env python3
from __future__ import annotations

"""
Stepwise runner (Phase 7) for the Growth System.

Responsibilities:
- Configure logging to both console and `logs/run.log`
- Load a YAML/JSON scenario and Phase 1 inputs
- Build the SD model (Phase 4/6 + Phase 7 sector signals)
- Apply scenario overrides (constants and lookup points)
- Phase 9: Echo applied overrides to `logs/` and enforce per-step validations:
  * `Agents_To_Create_<sector>` are non-negative integers
  * `Fulfillment_Ratio_<product>` remains within [0, 1]
  * Revenue identity holds each step (anchor + client equals combined)
- Execute a stepwise loop that:
  * reads `Agents_To_Create_<sector>` at current time
  * instantiates agents deterministically via sector factories
  * calls `act(...)` on all agents to produce per-product requirements
  * updates `Agent_Demand_Sector_Input_<sector>_<product>` numeric equations
  * advances the SD model one step via `run_step(step_index)`
  * logs optional DEBUG snapshots (gateways, fulfillment ratio, total demand)

Outputs:
- Phase 8 CSV (`output/Growth_System_Complete_Results.csv`) is generated at the end of a run.
"""

import argparse
import logging
import re
import shutil
from pathlib import Path

from src.io_paths import LOGS_DIR, SCENARIOS_DIR
from src.utils_logging import configure_logging
from src.phase1_data import load_phase1_inputs, apply_primary_map_overrides
from src.scenario_loader import load_and_validate_scenario, validate_overrides_against_model
from src.growth_model import build_phase4_model, apply_scenario_overrides
from src.abm_anchor import (
    build_all_anchor_agent_factories,
    build_sm_anchor_agent_factory,
)
from src.naming import (
    agents_to_create_converter,
    agent_demand_sector_input,
    total_demand,
    client_delivery_flow,
    anchor_delivery_flow_sector_product,
    anchor_delivery_flow_product,
    price_converter_product,
    c_stock,
    total_new_leads,
    anchor_lead_generation,
    cpc_stock,
    cumulative_agents_created,
    anchor_constant,
    client_creation_flow,
    potential_clients_stock,
    product_constant,
)
from BPTK_Py.modeling.simultaneousScheduler import SimultaneousScheduler
from src.kpi_extractor import RunGrid, extract_and_write_kpis, _safe_eval
from src.validation import (
    echo_scenario_overrides,
    sample_gateways,
    validate_agents_to_create_signals,
    validate_agents_to_create_sm_signals,
    validate_fulfillment_ratio_bounds,
    validate_revenue_identity,
)


def _capture_step_kpis(
    *,
    model,
    bundle,
    t: float,
    step_idx: int,
    agent_metrics_by_step: list[dict],
    sector_to_products: dict[str, list[str]],
    dt_years: float,
    include_sm_revenue_rows: bool = False,
    include_sm_client_rows: bool = False,
    sm_agents_by_pair: dict[tuple[str, str], list] | None = None,
) -> dict[str, float]:
    """Capture KPI values for the current step while gateway values are correct.

    Logic mirrors `kpi_extractor.collect_kpis_for_step` but is invoked DURING
    the stepwise loop, after ABM demand has been written to gateway converters
    and BEFORE advancing the scheduler. This ensures gateway-dependent values
    reflect the correct step state (avoids post-run corruption).

    Phase 17.6: When flags are enabled, also compute optional per-(sector, product)
    diagnostic rows for `Revenue <sector> <product>` and `Anchor Clients <sector> <product>`.
    Defaults keep these rows absent.
    """

    out: dict[str, float] = {}
    sectors: list[str] = list(bundle.lists.sectors)
    products: list[str] = list(bundle.lists.products)

    # ----- Product-level base series -----
    for m in products:
        td = _safe_eval(model, total_demand(m), t)
        cdf = _safe_eval(model, client_delivery_flow(m), t)
        adf_m = _safe_eval(model, anchor_delivery_flow_product(m), t)
        price = _safe_eval(model, price_converter_product(m), t)

        out[f"Order Basket {m}"] = td
        out[f"Order Delivery {m}"] = adf_m + cdf
        out[f"Revenue {m}"] = (adf_m + cdf) * price

        # Other Clients stock (cumulative clients by product)
        out[f"Other Clients {m}"] = _safe_eval(model, c_stock(m), t)

    # ----- Sector-level series -----
    for s in sectors:
        # Anchor Leads per sector reported as per-step (per-quarter if dt=0.25):
        # the model converter is per-year, so multiply by dt_years to get per-step units.
        # In SM-mode, sector-level lead generation doesn't exist; sum SM leads instead.
        try:
            val = _safe_eval(model, anchor_lead_generation(s), t) * float(dt_years)
        except Exception:
            # Sum per-(s,m) Anchor_Lead_Generation_<s>_<m> if sector-level missing
            sm_sum = 0.0
            for m in sector_to_products.get(s, []):
                try:
                    name_sm = f"Anchor_Lead_Generation_{s.replace(' ', '_')}_{m.replace(' ', '_')}"
                    sm_sum += float(model.evaluate_equation(name_sm, t)) * float(dt_years)
                except Exception:
                    continue
            val = sm_sum
        out[f"Anchor Leads {s}"] = val

        # Anchor revenue per sector = sum_p Anchor_Delivery_Flow_<s>_<p> * Price_<p>
        sector_rev = 0.0
        for m in sector_to_products.get(s, []):
            adf_sm = _safe_eval(model, anchor_delivery_flow_sector_product(s, m), t)
            price = _safe_eval(model, price_converter_product(m), t)
            sector_rev += adf_sm * price
        out[f"Revenue {s}"] = sector_rev

        # Optional per-(sector, product) revenue diagnostics
        if include_sm_revenue_rows:
            for m in sector_to_products.get(s, []):
                adf_sm_val = _safe_eval(model, anchor_delivery_flow_sector_product(s, m), t)
                price_val = _safe_eval(model, price_converter_product(m), t)
                out[f"Revenue {s} {m}"] = adf_sm_val * price_val

        # Anchor Clients and Active Projects per sector from runner-provided per-step metrics
        if step_idx < len(agent_metrics_by_step):
            step_metrics = agent_metrics_by_step[step_idx]
            active_value = float(step_metrics.get("active_by_sector", {}).get(s, 0))
            inprog_value = float(step_metrics.get("inprogress_by_sector", {}).get(s, 0))
            out[f"Anchor Clients {s}"] = active_value
            out[f"Active Projects {s}"] = inprog_value
        else:
            out[f"Anchor Clients {s}"] = 0.0
            out[f"Active Projects {s}"] = 0.0

    # ----- Totals across dimensions -----
    # Revenue total = sum product-level revenue
    out["Revenue"] = sum(out.get(f"Revenue {m}", 0.0) for m in products)

    # Anchor Leads total = sum sector-level per-quarter leads
    out["Anchor Leads"] = sum(out.get(f"Anchor Leads {s}", 0.0) for s in sectors)

    # Other Clients total = sum product-level C_<p> stocks
    out["Other Clients"] = sum(out.get(f"Other Clients {m}", 0.0) for m in products)

    # Other Leads total only (do not attribute to sectors to avoid duplication)
    # Report as per-step units by multiplying the per-year total leads by dt_years
    other_leads_total = 0.0
    for m in products:
        other_leads_total += _safe_eval(model, total_new_leads(m), t) * float(dt_years)
    out["Other Leads"] = other_leads_total

    # Order Basket total
    out["Order Basket"] = sum(out.get(f"Order Basket {m}", 0.0) for m in products)
    # Order Delivery total
    out["Order Delivery"] = sum(out.get(f"Order Delivery {m}", 0.0) for m in products)

    # Anchor Clients total and Active Projects total from per-step metrics
    if step_idx < len(agent_metrics_by_step):
        step_metrics = agent_metrics_by_step[step_idx]
        out["Anchor Clients"] = float(step_metrics.get("active_total", 0.0))
        out["Active Projects"] = float(step_metrics.get("inprogress_total", 0.0))
    else:
        out["Anchor Clients"] = 0.0
        out["Active Projects"] = 0.0

    # Optional per-(sector, product) anchor client diagnostics (primarily meaningful in SM-mode)
    if include_sm_client_rows:
        for s in sectors:
            for m in sector_to_products.get(s, []):
                key = f"Anchor Clients {s} {m}"
                val = 0.0
                # Only compute non-zero values when SM agents exist per pair
                if isinstance(sm_agents_by_pair, dict):
                    agents = sm_agents_by_pair.get((s, m), [])
                    cnt = 0
                    for agent in agents:
                        state_name = getattr(agent, "state", None)
                        if state_name is not None and str(state_name).endswith("ACTIVE"):
                            cnt += 1
                    val = float(cnt)
                out[key] = val

    return out


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the runner.

    Phase 11 adds a `--preset` option that maps to files under `scenarios/`.
    Exactly one of `--scenario` or `--preset` may be provided.
    The default resolves to the baseline scenario file.
    """
    p = argparse.ArgumentParser(description="Growth System – Runner (Phase 12: optional visualization)")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--scenario", type=str, help="Path to a scenario YAML/JSON file")
    group.add_argument(
        "--preset",
        type=str,
        help="Scenario preset name (resolves to file under 'scenarios/' directory, e.g., 'baseline' or 'price_shock')",
    )
    p.add_argument("--debug", action="store_true")
    # Phase 17.6 optional granular KPI rows
    p.add_argument(
        "--kpi-sm-revenue-rows",
        action="store_true",
        help="Include optional per-(sector, product) Revenue rows in the KPI CSV",
    )
    p.add_argument(
        "--kpi-sm-client-rows",
        action="store_true",
        help="Include optional per-(sector, product) Anchor Clients rows in the KPI CSV (mainly in SM-mode)",
    )
    p.add_argument(
        "--visualize",
        action="store_true",
        help="Generate plots from the produced KPI CSV and save under output/plots/",
    )
    return p.parse_args()


def _resolve_scenario_path(scenario: str | None, preset: str | None) -> Path:
    """Resolve the scenario file path from either an explicit path or a preset name.

    Rules:
    - If `scenario` is provided, return it as a `Path`.
    - If `preset` is provided, attempt `<preset>.yaml` then `<preset>.json` under `SCENARIOS_DIR`.
    - If neither provided, default to `baseline.yaml` under `SCENARIOS_DIR`.
    """
    if scenario:
        return Path(scenario)
    if preset:
        # Try YAML then JSON
        yaml_path = SCENARIOS_DIR / f"{preset}.yaml"
        json_path = SCENARIOS_DIR / f"{preset}.json"
        if yaml_path.exists():
            return yaml_path
        if json_path.exists():
            return json_path
        # Construct a helpful error with available presets
        available = sorted([p.stem for p in SCENARIOS_DIR.glob("*.yaml")] + [p.stem for p in SCENARIOS_DIR.glob("*.json")])
        raise FileNotFoundError(
            f"Preset '{preset}' not found under {SCENARIOS_DIR}. Available presets: {', '.join(available) or '(none)'}"
        )
    # Default
    return SCENARIOS_DIR / "baseline.yaml"


def load_scenario(path: Path, *, bundle):
    """Load and validate a scenario using Phase 3 strict rules.

    Returns the validated `Scenario` dataclass and logs basic details.
    """
    return load_and_validate_scenario(path, bundle=bundle)


def run_stepwise(
    bundle,
    scenario,
    *,
    log: logging.Logger,
    include_sm_revenue_rows: bool = False,
    include_sm_client_rows: bool = False,
) -> None:
    """Execute the Phase 7 stepwise simulation loop.

    This function builds the SD model, applies overrides, sets up sector agent
    factories, and then runs a deterministic step loop that updates the ABM→SD
    gateways each step before advancing the SD scheduler.

    The function focuses on correct ordering and internal validations; CSV
    generation is deferred to Phase 8.
    """
    # 1) Build SD model (includes Phase 4/6 + Phase 7 sector signals)
    build = build_phase4_model(bundle, scenario.runspecs)
    model = build.model

    # 2) Validate and then apply scenario overrides strictly by element name (no partials) and echo to logs
    validate_overrides_against_model(model, scenario)
    apply_scenario_overrides(model, scenario)
    echo_scenario_overrides(log_dir=LOGS_DIR, scenario=scenario, log=log)

    # 3) Build agent factories depending on anchor_mode
    anchor_mode = getattr(scenario.runspecs, "anchor_mode", "sector")
    factories = build_all_anchor_agent_factories(bundle)
    agents_by_sector: dict[str, list] = {s: [] for s in factories.keys()}
    sm_factories_by_pair: dict[tuple[str, str], callable] = {}
    sm_agents_by_pair: dict[tuple[str, str], list] = {}
    if anchor_mode == "sm":
        # Build per-(sector, product) factories for the explicit SM universe
        sm_df = getattr(bundle, "lists_sm", None)
        if sm_df is None or sm_df.empty:
            raise RuntimeError("SM-mode requested but lists_sm is empty or missing in inputs")
        sm_factories_by_pair.clear()
        sm_agents_by_pair.clear()
        for _, row in sm_df.iterrows():
            s = str(row["Sector"])
            m = str(row["Material"])
            sm_factories_by_pair[(s, m)] = build_sm_anchor_agent_factory(bundle, s, m)
            sm_agents_by_pair[(s, m)] = []

    # 4) Precompute sector→products mapping for gateway updates and
    #    product→sectors for revenue identity validation
    sector_to_products = bundle.primary_map.sector_to_materials
    product_to_sectors: dict[str, list[str]] = {}
    for sector, mats in sector_to_products.items():
        for m in mats:
            product_to_sectors.setdefault(m, []).append(sector)

    # 4a) Phase 14/17.4: Scenario seeding — instantiate ACTIVE agents at t0, adjust stock initials for gating/monitoring
    # Seeds are in addition to SD outflow. We also set CPC and Cumulative_Agents_Created
    # stock initial values so ATAM gating and monitoring reflect existing agents.
    seeds_active = getattr(scenario, "seeds_active_anchor_clients", None) or {}
    seeds_elapsed = getattr(scenario, "seeds_elapsed_quarters", None) or {}
    seeds_direct = getattr(scenario, "seeds_direct_clients", None) or {}
    seeds_active_sm = getattr(scenario, "seeds_active_anchor_clients_sm", None) or {}
    seeds_elapsed_sm = getattr(scenario, "seeds_elapsed_quarters_sm", None) or {}
    # New: completed projects backlog (sector and SM-mode)
    seeds_completed = getattr(scenario, "seeds_completed_projects", None) or {}
    seeds_completed_sm = getattr(scenario, "seeds_completed_projects_sm", None) or {}

    seeded_counts_by_sector: dict[str, int] = {}
    # We'll need start time and dt shortly; compute here for aging semantics
    start = float(scenario.runspecs.starttime)
    dt = float(scenario.runspecs.dt)

    if (seeds_active or seeds_completed) and anchor_mode != "sm":
        for sector, k in seeds_active.items():
            if k <= 0:
                continue
            factory = factories.get(sector)
            if factory is None:
                # This should have been validated by scenario loader; guard anyway
                log.error("Seeds provided for unknown or unmapped sector '%s' — skipping", sector)
                continue
            # Compute activation_time_years for aged seeds if provided
            elapsed_q = int(seeds_elapsed.get(sector, 0)) if isinstance(seeds_elapsed, dict) else 0
            activation_time_years = start - (elapsed_q * dt)
            # Instantiate and set ACTIVE state
            for _ in range(int(k)):
                agent = factory()
                # Immediate activation respecting aging
                try:
                    agent.state = getattr(agent, "state")  # ensure attribute exists
                    agent.activation_time_years = activation_time_years
                    # Force ACTIVE immediately
                    from src.abm_anchor import AnchorClientAgentState

                    agent.state = AnchorClientAgentState.ACTIVE
                except Exception:
                    # If agent API changes, fail fast
                    raise RuntimeError(f"Cannot set seeded agent ACTIVE state for sector '{sector}'")
                agents_by_sector[sector].append(agent)
            seeded_counts_by_sector[sector] = int(k)

            # Adjust SD stock initial values for gating/monitoring: CPC_<s> and Cumulative_Agents_Created_<s>
            try:
                cpc_elem = build.elements.get(cpc_stock(sector))
                cum_elem = build.elements.get(cumulative_agents_created(sector))
                for elem, val, label in (
                    (cpc_elem, float(k), "CPC"),
                    (cum_elem, float(k), "Cumulative_Agents_Created"),
                ):
                    if elem is not None and hasattr(elem, "initial_value"):
                        setattr(elem, "initial_value", val)
                    else:
                        log.debug(
                            "Phase 14: Could not set initial_value for %s_%s (element missing or lacks attribute); proceeding",
                            label,
                            sector,
                        )
            except Exception as e:
                log.debug("Phase 14: Seeding stock initial adjustment failed for sector %s: %s", sector, e)

        if seeded_counts_by_sector:
            log.info("Phase 14: Seeded ACTIVE anchor clients at t0: %s", seeded_counts_by_sector)

        # Phase 17.x: Convert completed-projects backlog into immediate ACTIVE anchors and remainder progress
        if seeds_completed:
            additional_active_by_sector: dict[str, int] = {}
            for sector, completed in seeds_completed.items():
                total_completed = int(completed)
                if total_completed <= 0:
                    continue
                # Determine per-agent threshold from inputs
                try:
                    # Use model constant to respect scenario overrides
                    name_ptc = anchor_constant("projects_to_client_conversion", sector)
                    const_obj = getattr(model, "constants", {}).get(name_ptc)
                    if const_obj is None:
                        raise KeyError(name_ptc)
                    ptc = int(round(float(getattr(const_obj, "equation", 0.0))))
                    if ptc <= 0:
                        raise ValueError("projects_to_client_conversion must be positive")
                except Exception as exc:
                    raise RuntimeError(f"Missing or invalid projects_to_client_conversion for sector '{sector}'") from exc
                num_active = total_completed // ptc
                # remainder = total_completed - num_active * ptc  # Remainder is discarded per design
                if num_active > 0:
                    factory = factories.get(sector)
                    if factory is None:
                        log.error("Completed-project seeds for unknown sector '%s' — skipping", sector)
                    else:
                        elapsed_q = int(seeds_elapsed.get(sector, 0)) if isinstance(seeds_elapsed, dict) else 0
                        activation_time_years = start - (elapsed_q * dt)
                        for _ in range(int(num_active)):
                            agent = factory()
                            try:
                                from src.abm_anchor import AnchorClientAgentState

                                agent.activation_time_years = activation_time_years
                                agent.state = AnchorClientAgentState.ACTIVE
                            except Exception:
                                raise RuntimeError(
                                    f"Cannot set ACTIVE on derived agent for sector '{sector}' from completed-project seeds"
                                )
                            agents_by_sector[sector].append(agent)
                        additional_active_by_sector[sector] = additional_active_by_sector.get(sector, 0) + int(num_active)
                        # Adjust SD monitoring/gating stocks by additional active
                        try:
                            add = float(num_active)
                            cpc_elem = build.elements.get(cpc_stock(sector))
                            cum_elem = build.elements.get(cumulative_agents_created(sector))
                            if cpc_elem is not None and hasattr(cpc_elem, "initial_value"):
                                prev = float(getattr(cpc_elem, "initial_value", 0.0) or 0.0)
                                setattr(cpc_elem, "initial_value", prev + add)
                            if cum_elem is not None and hasattr(cum_elem, "initial_value"):
                                prev = float(getattr(cum_elem, "initial_value", 0.0) or 0.0)
                                setattr(cum_elem, "initial_value", prev + add)
                        except Exception as e:
                            log.debug("Completed-project seeding stock init adjust failed for sector %s: %s", sector, e)
                # Discard remainder: per-agent progress is not fungible across agents
            if additional_active_by_sector:
                log.info("Phase 17.x: Derived ACTIVE anchors from completed-project seeds: %s", additional_active_by_sector)

    # SM-mode seeding: create ACTIVE agents per (s,m) and initialize CPC_<s>_<m> and Cumulative_Agents_Created_<s>_<m>
    if anchor_mode == "sm" and (seeds_active_sm or seeds_completed_sm):
        seeded_counts_by_pair: dict[tuple[str, str], int] = {}
        for sector, mat_map in seeds_active_sm.items():
            for material, k in mat_map.items():
                if k <= 0:
                    continue
                factory = sm_factories_by_pair.get((sector, material))
                if factory is None:
                    log.error("Seeds provided for unknown pair ('%s','%s') — skipping", sector, material)
                    continue
                activation_time_years = start - (int(seeds_elapsed.get(sector, 0)) * dt)
                for _ in range(int(k)):
                    agent = factory()
                    try:
                        from src.abm_anchor import AnchorClientAgentState

                        agent.activation_time_years = activation_time_years
                        agent.state = AnchorClientAgentState.ACTIVE
                    except Exception:
                        raise RuntimeError(f"Cannot set seeded SM agent ACTIVE state for ('{sector}', '{material}')")
                    sm_agents_by_pair[(sector, material)].append(agent)
                seeded_counts_by_pair[(sector, material)] = int(k)
                # Initialize SD stocks if present
                try:
                    cpc_name = f"CPC_{sector.replace(' ', '_')}_{material.replace(' ', '_')}"
                    cum_name = f"Cumulative_Agents_Created_{sector.replace(' ', '_')}_{material.replace(' ', '_')}"
                    cpc_elem = build.elements.get(cpc_name)
                    cum_elem = build.elements.get(cum_name)
                    if cpc_elem is not None and hasattr(cpc_elem, "initial_value"):
                        setattr(cpc_elem, "initial_value", float(k))
                    if cum_elem is not None and hasattr(cum_elem, "initial_value"):
                        setattr(cum_elem, "initial_value", float(k))
                except Exception as e:
                    log.debug("Phase 17.4: SM seeding stock initial adjustment failed for (%s,%s): %s", sector, material, e)
        if seeded_counts_by_pair:
            log.info("Phase 17.4: Seeded ACTIVE SM anchor clients at t0: %s", seeded_counts_by_pair)

        # Phase 17.x: SM completed projects → immediate ACTIVE agents and remainder per pair
        if seeds_completed_sm:
            additional_active_by_pair: dict[tuple[str, str], int] = {}
            for sector, mat_map in seeds_completed_sm.items():
                for material, completed in mat_map.items():
                    total_completed = int(completed)
                    if total_completed <= 0:
                        continue
                    factory = sm_factories_by_pair.get((sector, material))
                    if factory is None:
                        log.error("Completed-project seeds provided for unknown pair ('%s','%s') — skipping", sector, material)
                        continue
                    # Get per-(s,m) threshold from inputs.anchor_sm
                    try:
                        # Use model constant to respect scenario overrides
                        name_ptc_sm = f"projects_to_client_conversion_{sector.replace(' ', '_')}_{material.replace(' ', '_')}"
                        const_obj = getattr(model, "constants", {}).get(name_ptc_sm)
                        if const_obj is None:
                            raise KeyError(name_ptc_sm)
                        ptc = int(round(float(getattr(const_obj, "equation", 0.0))))
                        if ptc <= 0:
                            raise ValueError
                    except Exception:
                        raise RuntimeError(f"Missing projects_to_client_conversion for SM pair ('{sector}','{material}')")
                    num_active = total_completed // ptc
                    # remainder = total_completed - num_active * ptc  # Remainder is discarded per design
                    if num_active > 0:
                        # Apply SM aging if provided; otherwise active now
                        elapsed_q = (
                            int(seeds_elapsed_sm.get(sector, {}).get(material, 0)) if isinstance(seeds_elapsed_sm, dict) else 0
                        )
                        activation_time_years = start - (elapsed_q * dt)
                        for _ in range(int(num_active)):
                            agent = factory()
                            try:
                                from src.abm_anchor import AnchorClientAgentState

                                agent.activation_time_years = activation_time_years
                                agent.state = AnchorClientAgentState.ACTIVE
                            except Exception:
                                raise RuntimeError(f"Cannot set ACTIVE on derived SM agent for ('{sector}','{material}')")
                            sm_agents_by_pair[(sector, material)].append(agent)
                        additional_active_by_pair[(sector, material)] = additional_active_by_pair.get(
                            (sector, material), 0
                        ) + int(num_active)
                        # Initialize SD stocks by adding to existing initial_value
                        try:
                            add = float(num_active)
                            cpc_name = f"CPC_{sector.replace(' ', '_')}_{material.replace(' ', '_')}"
                            cum_name = f"Cumulative_Agents_Created_{sector.replace(' ', '_')}_{material.replace(' ', '_')}"
                            cpc_elem = build.elements.get(cpc_name)
                            cum_elem = build.elements.get(cum_name)
                            if cpc_elem is not None and hasattr(cpc_elem, "initial_value"):
                                prev = float(getattr(cpc_elem, "initial_value", 0.0) or 0.0)
                                setattr(cpc_elem, "initial_value", prev + add)
                            if cum_elem is not None and hasattr(cum_elem, "initial_value"):
                                prev = float(getattr(cum_elem, "initial_value", 0.0) or 0.0)
                                setattr(cum_elem, "initial_value", prev + add)
                        except Exception as e:
                            log.debug(
                                "SM completed-project seeding stock init adjust failed for (%s,%s): %s", sector, material, e
                            )
                    # Discard remainder for SM-mode as well
            if additional_active_by_pair:
                log.info("Phase 17.x: Derived ACTIVE SM anchors from completed-project seeds: %s", additional_active_by_pair)

    # Seed direct clients per product by initializing C_<p> stock and potential clients accumulator
    seeded_direct_by_product: dict[str, int] = {}
    if seeds_direct:
        for material, kdc in seeds_direct.items():
            if kdc <= 0:
                continue
            seeded_direct_by_product[material] = int(kdc)
            # Initialize C_<p> and Potential_Clients_<p> so discrete conversion logic is consistent
            try:
                c_elem = build.elements.get(c_stock(material))
                pc_elem = build.elements.get(potential_clients_stock(material))
                # Set cumulative clients to seeded value
                if c_elem is not None and hasattr(c_elem, "initial_value"):
                    setattr(c_elem, "initial_value", float(kdc))
                # Reset potential clients accumulator so no immediate extra fire
                if pc_elem is not None and hasattr(pc_elem, "initial_value"):
                    setattr(pc_elem, "initial_value", 0.0)
            except Exception as e:
                log.debug("Phase 14: Direct client seeding init failed for %s: %s", material, e)
        if seeded_direct_by_product:
            log.info("Phase 14: Seeded direct clients at t0: %s", seeded_direct_by_product)

    # 5) Determine step grid
    stop = float(scenario.runspecs.stoptime)
    num_steps = int(round((stop - start) / dt))
    if num_steps <= 0:
        raise ValueError("Non-positive number of steps computed from runspecs")

    log.info("Starting stepwise loop: %d steps from %.2f to %.2f (dt=%.2f)", num_steps, start, stop, dt)
    # Phase 17.6: Optional granular KPI rows
    if include_sm_revenue_rows or include_sm_client_rows:
        log.info(
            "Phase 17.6: Optional KPI rows enabled: revenue_sm=%s, clients_sm=%s",
            include_sm_revenue_rows,
            include_sm_client_rows,
        )

    # Persist per-step ABM metrics captured after agent.act(...) and before run_step
    agent_metrics_by_step: list[dict] = []
    # Persist per-step KPI values captured during the run when gateway values are correct
    kpi_values_by_step: list[dict[str, float]] = []

    # 6) Attach a proper BPTK_Py scheduler and run strictly with run_step
    # Using the standard SimultaneousScheduler per BPTK_Py.
    model.scheduler = SimultaneousScheduler()
    if getattr(model, "scheduler", None) is None:
        raise RuntimeError("BPTK_Py scheduler could not be initialized; cannot proceed with stepwise run")

    # Track lookups we've already warned about (per direction) to avoid spam
    warned_lookup_extrapolations: set[tuple[str, str]] = set()

    # 7) Main step loop
    for step_idx in range(num_steps):
        t = start + dt * step_idx

        # 6a) Determine how many agents to create this step and instantiate
        created_this_step = 0
        if anchor_mode == "sm":
            # Validate and read per-(s,m) creation signals
            sm_pairs = list(sm_factories_by_pair.keys())
            validate_agents_to_create_sm_signals(model=model, pairs=sm_pairs, t=t, log=log)
            for (sector, material), factory in sm_factories_by_pair.items():
                name_to_create = f"Agents_To_Create_{sector.replace(' ', '_')}_{material.replace(' ', '_')}"
                try:
                    k = int(model.evaluate_equation(name_to_create, t))
                except Exception as exc:
                    raise RuntimeError(f"Failed to evaluate '{name_to_create}' at t={t}") from exc
                if k <= 0:
                    continue
                for _ in range(k):
                    sm_agents_by_pair[(sector, material)].append(factory())
                created_this_step += k
        else:
            # Sector-mode legacy path
            validate_agents_to_create_signals(model=model, sectors=factories.keys(), t=t, log=log)
            for sector, factory in factories.items():
                name_to_create = agents_to_create_converter(sector)
                try:
                    k = int(model.evaluate_equation(name_to_create, t))
                except Exception as exc:
                    raise RuntimeError(f"Failed to evaluate '{name_to_create}' at t={t}") from exc
                if k <= 0:
                    continue
                for _ in range(k):
                    agents_by_sector[sector].append(factory())
                created_this_step += k

        # NOTE: ABM KPI capture moved to after agent.act(...) and before model.run_step

        # 6b) Agent actions and per-sector–material aggregation
        # Map (sector, material) -> aggregated requirement value
        agg_sm: dict[tuple[str, str], float] = {}
        if anchor_mode == "sm":
            # Each agent belongs to a single (s,m)
            for (sector, material), agents in sm_agents_by_pair.items():
                if not agents:
                    continue
                for agent in agents:
                    reqs = agent.act(t, round_no=0, step_no=step_idx, dt_years=dt)
                    value = float(reqs.get(material, 0.0))
                    if value <= 0:
                        continue
                    agg_sm[(sector, material)] = agg_sm.get((sector, material), 0.0) + value
        else:
            # Legacy sector-mode agents produce per-material maps
            for sector, agents in agents_by_sector.items():
                if not agents:
                    continue
                for agent in agents:
                    reqs = agent.act(t, round_no=0, step_no=step_idx, dt_years=dt)
                    for product, value in reqs.items():
                        if value <= 0:
                            continue
                        if product not in sector_to_products.get(sector, []):
                            continue
                        agg_sm[(sector, product)] = agg_sm.get((sector, product), 0.0) + float(value)

        # --- ABM KPI capture point: after agent.act(...) and before SD run_step ---
        active_by_sector: dict[str, int] = {}
        inprogress_by_sector: dict[str, int] = {}
        active_total = 0
        inprogress_total = 0
        if anchor_mode == "sm":
            # Aggregate by sector from SM agents
            for sector in bundle.lists.sectors:
                active_count = 0
                inprog_count = 0
                # Sum across products for this sector
                for material in sector_to_products.get(sector, []):
                    agents = sm_agents_by_pair.get((sector, material), [])
                    for agent in agents:
                        state_name = getattr(agent, "state", None)
                        if state_name is not None and str(state_name).endswith("ACTIVE"):
                            active_count += 1
                        started = int(getattr(agent, "num_projects_started", 0))
                        completed = int(getattr(agent, "num_projects_completed", 0))
                        inprog_count += max(0, started - completed)
                active_by_sector[sector] = active_count
                inprogress_by_sector[sector] = inprog_count
                active_total += active_count
                inprogress_total += inprog_count
        else:
            for sector, agents in agents_by_sector.items():
                active_count = 0
                inprog_count = 0
                for agent in agents:
                    state_name = getattr(agent, "state", None)
                    if state_name is not None and str(state_name).endswith("ACTIVE"):
                        active_count += 1
                    started = int(getattr(agent, "num_projects_started", 0))
                    completed = int(getattr(agent, "num_projects_completed", 0))
                    inprog_count += max(0, started - completed)
                active_by_sector[sector] = active_count
                inprogress_by_sector[sector] = inprog_count
                active_total += active_count
                inprogress_total += inprog_count

        agent_metrics_by_step.append(
            {
                "t": t,
                "active_by_sector": active_by_sector,
                "inprogress_by_sector": inprogress_by_sector,
                "active_total": active_total,
                "inprogress_total": inprogress_total,
            }
        )

        # Log a concise snapshot every step at DEBUG level
        log.debug(
            "t=%.2f step=%d created=%d active=%s in_progress=%s",
            t,
            step_idx,
            created_this_step,
            active_by_sector,
            inprogress_by_sector,
        )

        # 6c) Update gateway converters for all known sector–product pairs
        # Set to 0.0 when absent to keep values deterministic across steps
        for sector, materials in sector_to_products.items():
            for material in materials:
                name_sm = agent_demand_sector_input(sector, material)
                value = float(agg_sm.get((sector, material), 0.0))
                if name_sm not in getattr(model, "converters", {}):
                    # Skip silently if mapping says sector uses material but converter is absent
                    continue
                model.converters[name_sm].equation = value

        # 6d) Capture KPI values NOW while gateway values are correct for this step
        # This prevents the corruption that occurs during post-run evaluation
        step_kpis = _capture_step_kpis(
            model=model,
            bundle=bundle,
            t=t,
            step_idx=step_idx,
            agent_metrics_by_step=agent_metrics_by_step,
            sector_to_products=sector_to_products,
            dt_years=dt,
            include_sm_revenue_rows=include_sm_revenue_rows,
            include_sm_client_rows=include_sm_client_rows,
            sm_agents_by_pair=sm_agents_by_pair if anchor_mode == "sm" else None,
        )
        kpi_values_by_step.append(step_kpis)

        # 7d) Advance the SD model one step using the attached scheduler
        model.run_step(step_idx, collect_data=False)

        # 7e) Light validation and occasional DEBUG snapshots + Phase 15 lookup tail warnings
        # Revenue identity
        validate_revenue_identity(
            model=model,
            products=bundle.lists.products,
            product_to_sectors=product_to_sectors,
            t=t,
        )

        # Additional sampling & fulfillment bounds (debug only)
        if step_idx < 4 or step_idx in (num_steps // 2, num_steps - 1):
            # Sample gateways for the first material
            sample_gateways(
                model=model,
                sector_to_products=sector_to_products,
                t=t,
                log=log,
                sample_products=bundle.lists.products[:1],
            )
            # CPC vs ATAM per sector
            for s in bundle.lists.sectors:
                try:
                    cpc_val = float(model.evaluate_equation(cpc_stock(s), t))
                    atam_val = float(model.evaluate_equation(anchor_constant("ATAM", s), t))
                    log.debug("t=%.2f CPC_%s=%.6f ATAM_%s=%.6f", t, s, cpc_val, s, atam_val)
                except Exception:
                    pass
            # CL vs TAM per product and Potential/C with Client_Creation
            for m in bundle.lists.products[:2]:
                try:
                    cl_name = f"CL_{str(m).replace(' ', '_')}"
                    cl_val = float(model.evaluate_equation(cl_name, t))
                    # TAM is a product-level constant
                    tam_val = float(model.evaluate_equation(product_constant("TAM", m), t))
                except Exception:
                    cl_val = 0.0
                    tam_val = 0.0
                try:
                    pc_val = float(model.evaluate_equation(potential_clients_stock(m), t))
                except Exception:
                    pc_val = 0.0
                try:
                    c_val = float(model.evaluate_equation(c_stock(m), t))
                except Exception:
                    c_val = 0.0
                try:
                    cc_val = float(model.evaluate_equation(client_creation_flow(m), t))
                except Exception:
                    cc_val = 0.0
                log.debug(
                    "t=%.2f %s: CL=%.6f TAM=%.6f PC=%.6f C=%.6f Client_Creation=%.6f",
                    t,
                    m,
                    cl_val,
                    tam_val,
                    pc_val,
                    c_val,
                    cc_val,
                )
        # Always validate FR bounds every step
        validate_fulfillment_ratio_bounds(model=model, products=bundle.lists.products, t=t, log=log)

        # Phase 15: Lookup extrapolation warnings (hold-last-value policy).
        # Detect when t is outside provided points for any lookup used this step.
        # Warn only once per (converter, direction) per run to reduce log spam.
        try:
            meta = getattr(model, "_lookup_points_meta", {})
            if isinstance(meta, dict):
                for conv_name, info in meta.items():
                    tmin = info.get("tmin")
                    tmax = info.get("tmax")
                    kind = info.get("kind", "lookup")
                    if tmin is not None and t < tmin - 1e-9:
                        key = (str(conv_name), "below")
                        if key not in warned_lookup_extrapolations:
                            warned_lookup_extrapolations.add(key)
                            log.warning(
                                "Phase 15: %s lookup '%s' extrapolated below range at t=%.2f (min=%.2f)",
                                kind,
                                conv_name,
                                t,
                                tmin,
                            )
                    if tmax is not None and t > tmax + 1e-9:
                        key = (str(conv_name), "above")
                        if key not in warned_lookup_extrapolations:
                            warned_lookup_extrapolations.add(key)
                            log.warning(
                                "Phase 15: %s lookup '%s' extrapolated above range at t=%.2f (max=%.2f)",
                                kind,
                                conv_name,
                                t,
                                tmax,
                            )
        except Exception:
            # Non-fatal; proceed silently
            pass

    log.info("Completed %d steps successfully.", num_steps)

    # 8) Phase 8/15: KPI extraction & CSV writer (all simulated steps)
    run_grid = RunGrid(start=start, dt=dt, num_steps=num_steps)
    output_path = extract_and_write_kpis(
        model=model,
        bundle=bundle,
        run_grid=run_grid,
        agents_by_sector=agents_by_sector,
        sector_to_products=sector_to_products,
        agent_metrics_by_step=agent_metrics_by_step,
        kpi_values_by_step=kpi_values_by_step,
        include_sm_revenue_rows=include_sm_revenue_rows,
        include_sm_client_rows=include_sm_client_rows,
    )
    log.info("Wrote KPI CSV to %s", output_path)

    # Phase 11 quality-of-life: also write a scenario-suffixed copy for comparisons
    # Keep default file for regression tests; add a second file with scenario name suffix.
    try:
        suffix = re.sub(r"[^0-9A-Za-z_]+", "_", str(scenario.name).strip().replace(" ", "_"))
        if suffix:
            suffixed = output_path.with_name(output_path.stem + f"_{suffix}" + output_path.suffix)
            shutil.copyfile(output_path, suffixed)
            log.info("Also wrote suffixed KPI CSV to %s", suffixed)
    except Exception as _e:
        # Non-fatal; default output already written
        log.debug("Could not write suffixed KPI CSV: %s", _e)

    # Return the main output path for optional post-processing such as visualization
    return output_path


def main() -> int:
    args = parse_args()
    configure_logging(LOGS_DIR, debug=args.debug)
    log = logging.getLogger("runner")

    scenario_path = _resolve_scenario_path(args.scenario, args.preset)

    # Load Phase 1 inputs first since scenario validation depends on permissible keys
    bundle = load_phase1_inputs()

    scenario = load_scenario(scenario_path, bundle=bundle)
    # If scenario provides lists_sm, apply it to the bundle before any SM validations/build
    try:
        from src.phase1_data import apply_lists_sm_override

        bundle = apply_lists_sm_override(bundle, scenario)
    except Exception as _e:
        # Non-fatal; will be validated later if in SM-mode
        pass
    # Phase 13: Apply primary_map overrides (if any) before building the model
    bundle = apply_primary_map_overrides(bundle, scenario)
    # Allow scenario per-(s,m) constants to satisfy SM coverage by merging them into bundle.anchor_sm
    try:
        from src.phase1_data import merge_scenario_sm_constants_into_bundle

        bundle = merge_scenario_sm_constants_into_bundle(bundle, scenario)
    except Exception as _e:
        # Non-fatal; if merge fails we proceed with existing bundle
        pass
    log.info("Loaded scenario '%s' from %s", scenario.name, scenario_path)
    log.info(
        "Runspecs: start %.2f, stop %.2f, dt %.2f",
        scenario.runspecs.starttime,
        scenario.runspecs.stoptime,
        scenario.runspecs.dt,
    )

    # Quick dependency check useful during Phase 0 to fail fast if environment
    # is missing key libraries. This also surfaces import-time errors early.
    try:
        import BPTK_Py  # noqa: F401
        import pandas  # noqa: F401
    except Exception as e:
        log.error("Dependency import failed: %s", e)
        raise

    # bundle already loaded above for scenario validation
    log.info(
        "Inputs loaded: %d sectors, %d products",
        len(bundle.lists.sectors),
        len(bundle.lists.products),
    )
    log.info("Anchor params shape: %s", bundle.anchor.by_sector.shape)
    log.info("Other params shape: %s", bundle.other.by_product.shape)
    log.info(
        "Production rows: %d, Pricing rows: %d",
        len(bundle.production.long),
        len(bundle.pricing.long),
    )
    log.info(
        "Primary products mapping: %d sectors with assignments",
        len(bundle.primary_map.sector_to_materials),
    )

    # Run the stepwise loop
    output_csv = run_stepwise(
        bundle,
        scenario,
        log=log,
        include_sm_revenue_rows=args.kpi_sm_revenue_rows,
        include_sm_client_rows=args.kpi_sm_client_rows,
    )

    # Optional Phase 12 visualization: read the produced CSV and generate plots
    if args.visualize:
        try:
            from viz.plots import generate_all_plots_from_csv
        except Exception as e:
            log.error("Visualization dependencies missing or import failed: %s", e)
            raise

        try:
            generate_all_plots_from_csv(output_csv)
            log.info("Phase 12 visualization complete. Plots saved under output/plots/")
        except Exception as e:
            log.error("Visualization failed: %s", e)
            raise

    print("OK: Phase 7 stepwise runner passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
