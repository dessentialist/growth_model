from __future__ import annotations

"""
Phase 4, 6 & 7 (prereqs) — SD Model: Direct Clients, Lookups, Gateways, 
Anchor Deliveries, Agent Creation Signals (BPTK_Py SD-DSL)

This module builds the System Dynamics (SD) portion required for:
Phase 4
- Per-material constants for direct clients
- Lead and client-conversion structure with accumulate-and-fire logic
- Average order quantity growth by material
- Client requirements with a lead-to-requirement delay (quarters, no dt scaling)
- Capacity and price lookups as time-varying converters
- Total demand and a fulfillment ratio
- Client delivery flow and revenue per material

Phase 6
- ABM→SD gateways per sector–material as numeric converters
- Aggregated agent demand per material and inclusion in Total_Demand
- Per sector–material delayed agent demand and anchor delivery flows
- Aggregated anchor delivery flow per material

Phase 7 prerequisites
- Anchor parameter constants for all sectors (to allow strict scenario overrides)
- Sector-level agent creation signal using accumulate-and-fire logic:
  `Agents_To_Create_<sector>` and related accumulator stock

Design principles
- All equations are expressed using BPTK_Py SD-DSL elements/operators
- No fallbacks or hard-coded defaults: values originate from Phase 1 bundle
- Element names exactly match `technical_architecture.md` (use `src.naming` helpers)
- Gateway converters for ABM (per sector–material) are numeric and default to 0.0
  until updated by the stepwise runner

Usage
- Call `build_phase4_model(bundle, runspecs)` to create and return a configured
  BPTK_Py `Model` and an index of created elements.
- Call `apply_scenario_overrides(model, scenario)` to set constants and replace
  lookup points for price/capacity before running.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from BPTK_Py import Model
from BPTK_Py.sddsl import functions as F

from .naming import (
    # constants & lookups
    price_converter_product,
    max_capacity_converter_product,
    product_constant,
    # material-level SD elements
    inbound_leads,
    outbound_leads,
    total_new_leads,
    potential_clients_stock,
    client_creation_flow,
    c_stock,
    avg_order_quantity,
    client_requirement,
    fulfillment_ratio,
    delayed_client_demand,
    client_delivery_flow,
    client_revenue,
    # ABM→SD gateway scaffolding
    agent_demand_sector_input,
    agent_aggregated_demand,
    total_demand,
    # Phase 6 anchor delivery names
    delayed_agent_demand as delayed_agent_demand_name,
    anchor_delivery_flow_sector_product,
    anchor_delivery_flow_product,
    # anchor constants
    anchor_constant,
    anchor_lead_generation,
    cpc_stock,
    new_pc_flow,
    agent_creation_accumulator,
    agent_creation_inflow,
    agent_creation_outflow,
    agents_to_create_converter,
    cumulative_agents_created,
    cumulative_inflow,
    # Phase 16 per (sector, material) constants
    anchor_constant_sm,
    # Phase 17.2 SM-mode creation helpers
    anchor_lead_generation_sm,
    cpc_stock_sm,
    new_pc_flow_sm,
    agent_creation_accumulator_sm,
    agent_creation_inflow_sm,
    agent_creation_outflow_sm,
    agents_to_create_converter_sm,
    cumulative_agents_created_sm,
    cumulative_inflow_sm,
)
from .phase1_data import Phase1Bundle
from .scenario_loader import RunSpecs, Scenario


def _apply_delay_with_offset(model: Model, input_element, delay_quarters) -> object:
    """
    Apply a delay with automatic offset correction for BPTK_Py delay function behavior.
    
    BPTK_Py's F.delay() function has a one-step offset: input at time T produces
    output at time T + delay + 1 step. To achieve the expected delay behavior
    where input at time T produces output at time T + delay, we subtract 1
    from the delay parameter.
    
    Parameters:
    - model: BPTK_Py Model instance
    - input_element: The input element to delay
    - delay_quarters: Desired delay in quarters (can be float or model element)
    
    Returns:
    - BPTK_Py delay expression with corrected timing
    """
    # For model elements (constants), we need to create a new constant with the offset
    if hasattr(delay_quarters, 'equation'):
        # It's a model element, create a new constant with the offset
        offset_name = f"{delay_quarters.name}_offset" if hasattr(delay_quarters, 'name') else "delay_offset"
        offset_constant = model.constant(offset_name)
        offset_constant.equation = F.max(0.0, delay_quarters - 1.0)
        return F.delay(model, input_element, offset_constant)
    else:
        # It's a float value, apply the offset directly
        corrected_delay = max(0.0, float(delay_quarters) - 1.0)
        return F.delay(model, input_element, corrected_delay)


@dataclass
class Phase4BuildResult:
    model: Model
    # Map element name → element object for convenient access and testing
    elements: Dict[str, object]


def _as_float(value) -> float:
    # Guard to ensure Constant assignment with primitive float
    return float(value)


def _eq_if_started_and_under_tam(
    model: Model,
    base_rate: object,
    start_year: object,
    cl_stock: object,
    tam: object,
):
    """Compose: base_rate * If(Time >= start_year, 1, 0) * If(CL < TAM, 1, 0)."""
    return base_rate * F.If(F.time() >= start_year, 1, 0) * F.If(cl_stock < tam, 1, 0)


def _round_down_positive(x):
    """Floor for non-negative values via round(x - 0.5).

    BPTK_Py exposes `Round` but not `Floor`. For the accumulate-and-fire logic,
    we only need floor for non-negative values, which we implement with a
    stable round-down trick.
    """
    return F.Round(x - 0.5, 0)


def _build_anchor_constants(model: Model, bundle: Phase1Bundle, elements: Dict[str, object]) -> None:
    """Create all anchor parameter constants for every sector.

    This enables strict scenario overrides by exact element name for any
    anchor parameter observed in Phase 1 inputs.
    """
    # Anchor parameters are wide: index = param names, columns = sectors
    for param in bundle.anchor.by_sector.index.astype(str):
        for sector in bundle.anchor.by_sector.columns.astype(str):
            const_name = anchor_constant(param, sector)
            # Avoid duplicate creation if called from multiple blocks
            if const_name in getattr(model, "constants", {}):
                elements[const_name] = model.constants[const_name]
                continue
            c = model.constant(const_name)
            try:
                value = bundle.anchor.by_sector.at[param, sector]
            except Exception as exc:
                raise ValueError(f"Missing anchor parameter '{param}' for sector '{sector}'") from exc
            c.equation = _as_float(value)
            elements[const_name] = c


def _build_sector_agent_creation_block(model: Model, bundle: Phase1Bundle, sector: str, elements: Dict[str, object]) -> None:
    """Create sector-level lead generation and agent creation signals.

    Elements (matching technical_architecture.md):
    - Anchor_Lead_Generation_<s>
    - CPC_<s> stock accumulating lead generation
    - New_PC_Flow_<s> = Anchor_Lead_Generation_<s> * lead_to_pc_conversion_rate_<s>
    - Agent_Creation_Accumulator_<s> stock
    - Agent_Creation_Inflow_<s> = New_PC_Flow_<s>
    - Agent_Creation_Outflow_<s> = floor_like(Agent_Creation_Accumulator_<s>)
    - Agents_To_Create_<s> (converter) same as outflow expression
    - Cumulative_Agents_Created_<s> stock with inflow = Agent_Creation_Outflow_<s>
    """
    # Ensure core constants exist for this sector (created once globally)
    for p in ("anchor_lead_generation_rate", "anchor_start_year", "ATAM", "lead_to_pc_conversion_rate"):
        name = anchor_constant(p, sector)
        if name not in getattr(model, "constants", {}):
            # Backfill constant if not yet created
            c = model.constant(name)
            c.equation = _as_float(bundle.anchor.by_sector.at[p, sector])
            elements[name] = c
        else:
            elements[name] = model.constants[name]

    rate = model.constants[anchor_constant("anchor_lead_generation_rate", sector)]
    start = model.constants[anchor_constant("anchor_start_year", sector)]
    atam = model.constants[anchor_constant("ATAM", sector)]
    conv = model.constants[anchor_constant("lead_to_pc_conversion_rate", sector)]

    # Lead generation gated by start year and ATAM via CPC stock
    cpc_name = cpc_stock(sector)
    cpc = model.stock(cpc_name)
    elements[cpc_name] = cpc

    alg_name = anchor_lead_generation(sector)
    alg = model.converter(alg_name)
    # Scale per-quarter anchor lead generation to per-year by multiplying by 4.
    # With dt = 0.25 years (one quarter), the CPC stock increments by the intended
    # per-quarter amount each step: (4 * rate_per_quarter) * 0.25 years = rate_per_quarter.
    alg.equation = 4 * rate * F.If(F.time() >= start, 1, 0) * F.If(cpc < atam, 1, 0)
    elements[alg_name] = alg

    # CPC accumulates anchor leads
    cpc.equation = alg

    # New_PC_Flow
    newpc_name = new_pc_flow(sector)
    newpc = model.converter(newpc_name)
    newpc.equation = alg * conv
    elements[newpc_name] = newpc

    # Accumulate-and-fire structure for integer agent creation
    acc_name = agent_creation_accumulator(sector)
    acc = model.stock(acc_name)
    elements[acc_name] = acc

    inflow_name = agent_creation_inflow(sector)
    inflow = model.converter(inflow_name)
    inflow.equation = newpc
    elements[inflow_name] = inflow

    # floor_like via round(x - 0.5, 0) and clamp to >= 0
    outflow_expr = F.max(0, _round_down_positive(acc))

    outflow_name = agent_creation_outflow(sector)
    outflow = model.converter(outflow_name)
    outflow.equation = outflow_expr
    elements[outflow_name] = outflow

    # Dedicated drain converter used only in the stock derivative to realize
    # whole-per-quarter decrements when dt=0.25 years.
    drain_name = f"Agent_Creation_Drain_{sector.replace(' ', '_')}"
    drain = model.converter(drain_name)
    # Multiply integer outflow by 4 so that integrated change per step is integer
    # (4 * k) * 0.25 years = k
    drain.equation = 4 * outflow
    elements[drain_name] = drain

    # Stock net = inflow - drain (ensures one whole unit per quarter event)
    acc.equation = inflow - drain

    # Convenience converter equals outflow (integer creations this step)
    to_create_name = agents_to_create_converter(sector)
    to_create = model.converter(to_create_name)
    to_create.equation = outflow_expr
    elements[to_create_name] = to_create

    # Cumulative created (monitoring). Use the same drain so the cumulative stock
    # integrates the integer number of creations per quarter step.
    cum_in_name = cumulative_inflow(sector)
    cum_in = model.converter(cum_in_name)
    cum_in.equation = drain
    elements[cum_in_name] = cum_in

    cum_name = cumulative_agents_created(sector)
    cum = model.stock(cum_name)
    cum.equation = cum_in
    elements[cum_name] = cum


def _require_anchor_sm_value(bundle: Phase1Bundle, sector: str, material: str, param: str) -> float:
    """Fetch a per-(sector, material) anchor parameter value strictly from `bundle.anchor_sm`.

    Used in SM-mode where 17.1 requires complete per-(s,m) coverage. Any missing
    (sector, material, param) triple is a hard error to surface input gaps early.
    """
    sm_df = getattr(bundle, "anchor_sm", None)
    if sm_df is None or sm_df.empty:
        raise ValueError("SM-mode requires anchor_params_sm; none loaded")
    sel = sm_df[
        (sm_df["Sector"].astype(str) == str(sector))
        & (sm_df["Material"].astype(str) == str(material))
        & (sm_df["Param"].astype(str) == str(param))
    ]
    if sel.empty:
        raise ValueError(f"Missing per-(sector, material) parameter ({sector}, {material}, {param}) for SM-mode")
    return float(sel.iloc[0]["Value"])


def _ensure_sm_anchor_constants_for_pair(
    model: Model, bundle: Phase1Bundle, sector: str, material: str, elements: Dict[str, object]
) -> None:
    """Ensure all SM-mode per-(s,m) anchor constants exist for a pair.

    - Creates constants for the full 17.1 set.
    - Values are strictly read from `bundle.anchor_sm` (no sector-level fallback in SM-mode).
    - Missing values raise with a precise message naming the triple.
    """
    required_params = (
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
    )
    const_map = getattr(model, "constants", {})
    for p in required_params:
        name_sm = anchor_constant_sm(p, sector, material)
        if name_sm in const_map:
            elements[name_sm] = const_map[name_sm]
            continue
        c = model.constant(name_sm)
        c.equation = _as_float(_require_anchor_sm_value(bundle, sector, material, p))
        elements[name_sm] = c


def _build_sm_agent_creation_block(
    model: Model, bundle: Phase1Bundle, sector: str, material: str, elements: Dict[str, object]
) -> None:
    """Build SM-mode per-(s,m) lead generation and accumulate-and-fire creation signals.

    Elements created (Phase 17.2):
    - `Anchor_Lead_Generation_<s>_<m>` (scaled by 4 for dt=0.25 integration)
    - `CPC_<s>_<m>` stock integrating anchor leads
    - `New_PC_Flow_<s>_<m>`
    - `Agent_Creation_Accumulator_<s>_<m>` stock with inflow minus a 4× drain of the integerized outflow
    - `Agent_Creation_Inflow_<s>_<m>`, `Agent_Creation_Outflow_<s>_<m>` (floor-like via Round(x-0.5))
    - `Agents_To_Create_<s>_<m>` (integer creations this step)
    - `Cumulative_Agents_Created_<s>_<m>` stock integrating the drained outflow
    """
    # Ensure all needed per-(s,m) constants exist
    _ensure_sm_anchor_constants_for_pair(model, bundle, sector, material, elements)

    # Short-hands for constants
    rate = model.constants[anchor_constant_sm("anchor_lead_generation_rate", sector, material)]
    start = model.constants[anchor_constant_sm("anchor_start_year", sector, material)]
    atam = model.constants[anchor_constant_sm("ATAM", sector, material)]
    conv = model.constants[anchor_constant_sm("lead_to_pc_conversion_rate", sector, material)]

    # CPC stock
    cpc_name = cpc_stock_sm(sector, material)
    cpc = model.stock(cpc_name)
    elements[cpc_name] = cpc

    # Lead generation (scaled by 4 for per-year integration with dt=0.25)
    alg_name = anchor_lead_generation_sm(sector, material)
    alg = model.converter(alg_name)
    alg.equation = 4 * rate * F.If(F.time() >= start, 1, 0) * F.If(cpc < atam, 1, 0)
    elements[alg_name] = alg

    # CPC integrates lead generation
    cpc.equation = alg

    # New_PC_Flow
    newpc_name = new_pc_flow_sm(sector, material)
    newpc = model.converter(newpc_name)
    newpc.equation = alg * conv
    elements[newpc_name] = newpc

    # Accumulate-and-fire structure
    acc_name = agent_creation_accumulator_sm(sector, material)
    acc = model.stock(acc_name)
    elements[acc_name] = acc

    inflow_name = agent_creation_inflow_sm(sector, material)
    inflow = model.converter(inflow_name)
    inflow.equation = newpc
    elements[inflow_name] = inflow

    outflow_expr = F.max(0, _round_down_positive(acc))

    outflow_name = agent_creation_outflow_sm(sector, material)
    outflow = model.converter(outflow_name)
    outflow.equation = outflow_expr
    elements[outflow_name] = outflow

    drain_name = f"Agent_Creation_Drain_{sector.replace(' ', '_')}_{material.replace(' ', '_')}"
    drain = model.converter(drain_name)
    drain.equation = 4 * outflow
    elements[drain_name] = drain

    # Stock net = inflow - drain
    acc.equation = inflow - drain

    # Agents_To_Create_<s>_<m>
    to_create_name = agents_to_create_converter_sm(sector, material)
    to_create = model.converter(to_create_name)
    to_create.equation = outflow_expr
    elements[to_create_name] = to_create

    # Cumulative created stock
    cum_in_name = cumulative_inflow_sm(sector, material)
    cum_in = model.converter(cum_in_name)
    cum_in.equation = drain
    elements[cum_in_name] = cum_in

    cum_name = cumulative_agents_created_sm(sector, material)
    cum = model.stock(cum_name)
    cum.equation = cum_in
    elements[cum_name] = cum


def _build_product_block(
    model: Model,
    bundle: Phase1Bundle,
    material: str,
    elements: Dict[str, object],
    *,
    anchor_mode: str = "sector",
) -> None:
    """Create all SD elements for a single product and its sector couplings.

    Parameters
    ----------
    anchor_mode : {"sector", "sm"}
        Controls how per-(sector, material) constants are sourced for anchor
        requirement phase parameters and lags:
        - sector (legacy): use per-(s,m) value if provided in `anchor_params_sm`,
          else fall back to sector-level anchor parameters (Phase 16 precedence).
        - sm (strict): require per-(s,m) values for all targeted parameters and
          lags; sector-level fallbacks are disabled (Phase 17.5 enforcement).
    """
    """Create all Phase 4 SD elements for a single product.

    Element names exactly match helpers from `src.naming`.
    """
    # ---- Constants (direct client parameters) ----
    # All these constants exist as per Phase 1 inputs (Other Client Parameters)
    # Note: The inputs file uses a row label 'TAM' (not 'TAM_material').
    # We strictly honor the CSV schema discovered in Phase 1.
    const_names = {
        "lead_start_year": product_constant("lead_start_year", material),
        "inbound_lead_generation_rate": product_constant("inbound_lead_generation_rate", material),
        "outbound_lead_generation_rate": product_constant("outbound_lead_generation_rate", material),
        "lead_to_c_conversion_rate": product_constant("lead_to_c_conversion_rate", material),
        "lead_to_requirement_delay": product_constant("lead_to_requirement_delay", material),
        "requirement_to_fulfilment_delay": product_constant("requirement_to_fulfilment_delay", material),
        "avg_order_quantity_initial": product_constant("avg_order_quantity_initial", material),
        "client_requirement_growth": product_constant("client_requirement_growth", material),
        # CSV row name is 'TAM' in provided inputs (not 'TAM_material')
        "TAM": product_constant("TAM", material),
    }
    for key, const_name in const_names.items():
        c = model.constant(const_name)
        # Fill with numeric from Phase 1 OtherParams
        try:
            value = bundle.other.by_product.loc[key, material]
        except KeyError as exc:  # strict policy: must exist
            raise ValueError(f"Missing other client parameter '{key}' for material '{material}'") from exc
        c.equation = _as_float(value)
        elements[const_name] = c

    # Short hands to improve equation readability
    lead_start = elements[const_names["lead_start_year"]]
    in_rate = elements[const_names["inbound_lead_generation_rate"]]
    out_rate = elements[const_names["outbound_lead_generation_rate"]]
    conv_rate = elements[const_names["lead_to_c_conversion_rate"]]
    delay_lr = elements[const_names["lead_to_requirement_delay"]]
    delay_cf = elements[const_names["requirement_to_fulfilment_delay"]]
    avg_initial = elements[const_names["avg_order_quantity_initial"]]
    growth = elements[const_names["client_requirement_growth"]]
    tam = elements[const_names["TAM"]]

    # ---- Leads accumulator for TAM gating (CL_<m>) ----
    cl_name = f"CL_{material.replace(' ', '_')}"
    cl_stock = model.stock(cl_name)
    elements[cl_name] = cl_stock

    # ---- Inbound/Outbound Leads converters ----
    inbound_name = inbound_leads(material)
    outbound_name = outbound_leads(material)
    inbound = model.converter(inbound_name)
    outbound = model.converter(outbound_name)
    # Scale per-quarter lead rates to per-year by multiplying by 4 so that with dt=0.25
    # the integrated increment per step equals the intended per-quarter rate.
    inbound.equation = 4 * _eq_if_started_and_under_tam(model, in_rate, lead_start, cl_stock, tam)
    outbound.equation = 4 * _eq_if_started_and_under_tam(model, out_rate, lead_start, cl_stock, tam)
    elements[inbound_name] = inbound
    elements[outbound_name] = outbound

    # ---- Total_New_Leads and Fractional conversion ----
    total_new_name = total_new_leads(material)
    total_new = model.converter(total_new_name)
    total_new.equation = inbound + outbound
    elements[total_new_name] = total_new

    frac_conv_name = f"Fractional_Client_Conversion_{material.replace(' ', '_')}"
    frac_conv = model.converter(frac_conv_name)
    frac_conv.equation = total_new * conv_rate
    elements[frac_conv_name] = frac_conv

    # ---- Accumulate-and-fire discrete client creation ----
    pc_name = potential_clients_stock(material)
    pc = model.stock(pc_name)
    elements[pc_name] = pc

    cc_name = client_creation_flow(material)
    cc = model.converter(cc_name)
    cc.equation = F.max(0, _round_down_positive(pc))
    elements[cc_name] = cc

    # Dedicated drain converter for integer client creations, used only in stock derivatives
    cc_drain_name = f"Client_Creation_Drain_{material.replace(' ', '_')}"
    cc_drain = model.converter(cc_drain_name)
    cc_drain.equation = 4 * cc
    elements[cc_drain_name] = cc_drain

    # Potential_Clients accumulates fractional conversions minus drained integer creations
    pc.equation = frac_conv - cc_drain

    # C_<m> accumulates created clients using the drained integer flow
    c_name = c_stock(material)
    c_clients = model.stock(c_name)
    c_clients.equation = cc_drain
    elements[c_name] = c_clients

    # CL_<m> accumulates total new leads (for TAM gating threshold)
    cl_stock.equation = total_new

    # ---- Average order quantity growth ----
    # avg_order_quantity_<m> = avg_order_quantity_initial_<m> * 
    #   (1 + client_requirement_growth_<m>)^(max(0, Time - lead_start_year_<m>))
    avg_name = avg_order_quantity(material)
    avg = model.converter(avg_name)
    # Client requirement growth is per quarter: exponent must count elapsed quarters.
    quarters_since_start = F.max(0, (F.time() - lead_start) / 0.25)
    avg.equation = avg_initial * (1 + growth) ** quarters_since_start
    elements[avg_name] = avg

    # ---- Client Requirement with cohort aging chain and per-client cap ----
    # Default behavior: cohort-based system with per-client order limits
    req_name = client_requirement(material)
    req = model.converter(req_name)
    
    # Per-client cap parameter (default 10x base order quantity)
    limit_mult_name = product_constant("requirement_limit_multiplier", material)
    limit_mult = model.constant(limit_mult_name)
    limit_mult.equation = _as_float(10.0)  # Default 10x cap
    elements[limit_mult_name] = limit_mult

    # Build aging chain sized to run horizon. One bucket per simulated quarter step.
    # Clients created this step enter Cohort_0, then shift +1 bucket per step.
    # Stock dynamics (dt in years): dC0/dt = (1/dt)*N_t - (1/dt)*C0; dCa/dt = (1/dt)*C{a-1} - (1/dt)*Ca
    # With dt=0.25, (1/dt)=4 ensures exact quarter shifting.
    num_steps_float = max(1.0, (float(model.stoptime) - float(model.starttime)) / float(model.dt))
    num_buckets = int(num_steps_float + 1e-9)
    cohort_stocks = []

    # Inflow uses the drained integer creations (per-year units): Client_Creation_Drain_<m> = 4 * Client_Creation_<m>
    cc_drain_name = f"Client_Creation_Drain_{material.replace(' ', '_')}"
    cc_drain = elements[cc_drain_name]

    # Quarter-shift rate in per-year units
    shift_rate = _as_float(1.0 / float(model.dt))  # typically 4.0

    for age in range(num_buckets):
        cohort_name = f"Direct_Client_Cohort_{age}_{material.replace(' ', '_')}"
        inflow_name = f"Direct_Client_Cohort_Inflow_{age}_{material.replace(' ', '_')}"
        outflow_name = f"Direct_Client_Cohort_Outflow_{age}_{material.replace(' ', '_')}"

        cohort = model.stock(cohort_name)
        inflow_conv = model.converter(inflow_name)
        outflow_conv = model.converter(outflow_name)

        if age == 0:
            # New creations enter here, then shift to age 1 next step
            inflow_conv.equation = cc_drain
            outflow_conv.equation = shift_rate * cohort
        elif age < num_buckets - 1:
            # Intermediate buckets: shift in from previous, shift out to next
            prev = cohort_stocks[age - 1]
            inflow_conv.equation = shift_rate * prev
            outflow_conv.equation = shift_rate * cohort
        else:
            # Terminal bucket: accumulates all remaining clients without further outflow
            prev = cohort_stocks[age - 1]
            inflow_conv.equation = shift_rate * prev
            outflow_conv.equation = 0.0

        cohort.equation = inflow_conv - outflow_conv
        elements[cohort_name] = cohort
        elements[inflow_name] = inflow_conv
        elements[outflow_name] = outflow_conv
        cohort_stocks.append(cohort)

    # Linear per-client growth by cohort age with per-client cap
    # per_client_order(age) = min(B + (B * growth) * age, B * requirement_limit_multiplier)
    # Total order this step = sum_over_ages( cohort_size(age) * per_client_order(age) )
    cohort_orders_name = f"Cohort_Effective_Orders_{material.replace(' ', '_')}"
    cohort_orders = model.converter(cohort_orders_name)
    # Build chained sum expression to stay within DSL
    if cohort_stocks:
        # Precompute common terms
        per_client_cap = avg_initial * limit_mult
        expr_sum = None
        for idx, cohort in enumerate(cohort_stocks):
            age_scalar = _as_float(float(idx))
            per_client_linear = avg_initial + (avg_initial * growth) * age_scalar
            per_client_capped = F.min(per_client_linear, per_client_cap)
            term = cohort * per_client_capped
            expr_sum = term if expr_sum is None else (expr_sum + term)
        cohort_orders.equation = expr_sum if expr_sum is not None else 0.0
    else:
        cohort_orders.equation = 0.0
    elements[cohort_orders_name] = cohort_orders

    # Apply delay to cohort orders directly
    req.equation = _apply_delay_with_offset(model, cohort_orders, delay_lr)
    elements[req_name] = req

    # ---- Lookups: capacity and price ----
    # max_capacity_lookup_<m> = lookup(time, max_capacity_<m>)
    cap_conv_name = max_capacity_converter_product(material)
    price_conv_name = price_converter_product(material)

    cap_conv = model.converter(cap_conv_name)
    price_conv = model.converter(price_conv_name)

    # Build points from Phase 1 tables for this material. We embed points
    # directly into the converter equation via F.lookup(F.time(), points) and
    # allow scenario overrides to reassign these points later.
    cap_points: List[Tuple[float, float]] = [
        (float(row["Year"]), float(row["Capacity"]))
        for _, row in bundle.production.long[bundle.production.long["Material"] == material].iterrows()
    ]
    price_points: List[Tuple[float, float]] = [
        (float(row["Year"]), float(row["Price"]))
        for _, row in bundle.pricing.long[bundle.pricing.long["Material"] == material].iterrows()
    ]

    # Store a small reference to points under model for later override application
    # Note: we do not create elements for raw lookup tables; points live in the equation operator
    # Production capacity input is provided in kg/year. The SD model operates
    # on a quarter step (dt = 0.25 years) and demand flows are expressed per
    # quarter. Convert capacity to a per-quarter basis by dividing by 4 so it
    # is comparable to per-quarter demand in the fulfillment ratio.
    cap_conv.equation = F.lookup(F.time(), cap_points) / 4.0
    price_conv.equation = F.lookup(F.time(), price_points)
    elements[cap_conv_name] = cap_conv
    elements[price_conv_name] = price_conv

    # Record lookup metadata on the model to support Phase 15 extrapolation warnings
    # Structure: model._lookup_points_meta[converter_name] = 
    #   {"points": [(t,v)...], "tmin":, "tmax":, "kind": "capacity"|"price"}
    meta = getattr(model, "_lookup_points_meta", None)
    if meta is None:
        meta = {}
        setattr(model, "_lookup_points_meta", meta)
    if cap_points:
        meta[cap_conv_name] = {
            "points": cap_points,
            "tmin": min(p[0] for p in cap_points),
            "tmax": max(p[0] for p in cap_points),
            "kind": "capacity",
        }
    if price_points:
        meta[price_conv_name] = {
            "points": price_points,
            "tmin": min(p[0] for p in price_points),
            "tmax": max(p[0] for p in price_points),
            "kind": "price",
        }

    # ---- ABM→SD gateways and anchor deliveries (Phase 6) ----
    # Numeric converters per sector–material pair default to 0.0 and can be
    # updated by the runner each step without recompilation.
    # Also create per-material aggregation and total demand including direct clients.

    # Identify sectors that use this material from Primary Material map
    sectors_using_material = (
        bundle.primary_map.long[bundle.primary_map.long["Material"] == material]["Sector"].unique().tolist()
    )
    sector_inputs: List[object] = []
    for sector in sectors_using_material:
        name_sm = agent_demand_sector_input(sector, material)
        g = model.converter(name_sm)
        g.equation = 0.0
        elements[name_sm] = g
        sector_inputs.append(g)

    # Aggregated agent demand per material
    agg_name = agent_aggregated_demand(material)
    agg = model.converter(agg_name)
    # Avoid Python sum() on DSL elements (can coerce to Python numbers). Build
    # a chained expression using + so the result remains an SD-DSL expression.
    if not sector_inputs:
        agg.equation = 0.0
    else:
        expr = sector_inputs[0]
        for s in sector_inputs[1:]:
            expr = expr + s
        agg.equation = expr
    elements[agg_name] = agg

    # Total demand = Aggregated agent demand + Client requirement
    td_name = total_demand(material)
    td = model.converter(td_name)
    td.equation = agg + req
    elements[td_name] = td

    # Fulfillment ratio = min(1, if Total_Demand > 0 then capacity/Total_Demand else 1)
    fr_name = fulfillment_ratio(material)
    fr = model.converter(fr_name)
    fr.equation = F.min(1, F.If(td > 0, cap_conv / td, 1))
    elements[fr_name] = fr

    # Client delivery and revenue
    dcd_name = delayed_client_demand(material)
    dcd = model.converter(dcd_name)
    dcd.equation = req * fr
    elements[dcd_name] = dcd

    cdf_name = client_delivery_flow(material)
    cdf = model.converter(cdf_name)
    cdf.equation = _apply_delay_with_offset(model, dcd, delay_cf)
    elements[cdf_name] = cdf

    rev_name = client_revenue(material)
    rev = model.converter(rev_name)
    rev.equation = cdf * price_conv
    elements[rev_name] = rev

    # ---- Phase 6: Anchor delayed demand and deliveries ----
    delayed_sector_converters: List[object] = []
    sector_delivery_converters: List[object] = []

    for sector in sectors_using_material:
        # Phase 16/17: Create per-(s,m) constants for requirement phase parameters.
        # - SM-mode (Phase 17.5 strict): MUST come from anchor_params_sm; no sector fallback.
        # - Sector-mode (legacy): fallback to sector-level values when (s,m) not provided.
        sm_params = (
            "initial_requirement_rate",
            "initial_req_growth",
            "ramp_requirement_rate",
            "ramp_req_growth",
            "steady_requirement_rate",
            "steady_req_growth",
        )
        for p in sm_params:
            name_sm = anchor_constant_sm(p, sector, material)
            if anchor_mode == "sm":
                # Strict: require per-(s,m) value
                value = _require_anchor_sm_value(bundle, sector, material, p)
            else:
                # Legacy: use (s,m) if present, else sector-level
                use_val = None
                sm_df = getattr(bundle, "anchor_sm", None)
                if sm_df is not None and not sm_df.empty:
                    selp = sm_df[
                        (sm_df["Sector"].astype(str) == str(sector))
                        & (sm_df["Material"].astype(str) == str(material))
                        & (sm_df["Param"].astype(str) == str(p))
                    ]
                    if not selp.empty:
                        use_val = float(selp.iloc[0]["Value"])
                if use_val is None:
                    try:
                        use_val = _as_float(bundle.anchor.by_sector.at[p, sector])
                    except Exception as exc:
                        raise ValueError(
                            f"Missing anchor parameter '{p}' for sector '{sector}' (required for per-(s,m) constants)"
                        ) from exc
                value = use_val
            c_sm = model.constant(name_sm)
            c_sm.equation = _as_float(value)
            elements[name_sm] = c_sm

        # Phase 16/17: per-(s,m) requirement_to_order_lag constant
        # - SM-mode: strict per-(s,m); sector fallback disabled
        # - Sector-mode: preserve prior precedence (per-(s,m) if present, else sector)
        rtol_sm_name = anchor_constant_sm("requirement_to_order_lag", sector, material)
        const_map = getattr(model, "constants", {})
        if anchor_mode == "sm":
            use_value = _require_anchor_sm_value(bundle, sector, material, "requirement_to_order_lag")
        else:
            # Legacy fallback to sector-level when (s,m) not provided
            sm_df = getattr(bundle, "anchor_sm", None)
            use_value = None
            if sm_df is not None and not sm_df.empty:
                sel = sm_df[
                    (sm_df["Sector"].astype(str) == str(sector))
                    & (sm_df["Material"].astype(str) == str(material))
                    & (sm_df["Param"].astype(str) == "requirement_to_order_lag")
                ]
                if not sel.empty:
                    use_value = float(sel.iloc[0]["Value"])
            if use_value is None:
                try:
                    use_value = _as_float(bundle.anchor.by_sector.at["requirement_to_order_lag", sector])
                except Exception as exc:
                    raise ValueError(f"Missing anchor parameter 'requirement_to_order_lag' for sector '{sector}'") from exc
        if rtol_sm_name not in const_map:
            rtol_sm = model.constant(rtol_sm_name)
            rtol_sm.equation = _as_float(use_value)
            elements[rtol_sm_name] = rtol_sm
        else:
            elements[rtol_sm_name] = const_map[rtol_sm_name]
        rtol_element_name_to_use = rtol_sm_name

        # Delayed_Agent_Demand_<s>_<m> = Agent_Demand_Sector_Input_<s>_<m> * Fulfillment_Ratio_<m>
        delayed_name = delayed_agent_demand_name(sector, material)
        delayed_conv = model.converter(delayed_name)
        delayed_conv.equation = model.converters[agent_demand_sector_input(sector, material)] * fr
        elements[delayed_name] = delayed_conv
        delayed_sector_converters.append(delayed_conv)

        # Anchor_Delivery_Flow_<s>_<m> = delay(model, Delayed_Agent_Demand_<s>_<m>, requirement_to_order_lag_<s>)
        adf_sm_name = anchor_delivery_flow_sector_product(sector, material)
        adf_sm = model.converter(adf_sm_name)
        # Apply delay with offset correction for BPTK_Py timing behavior
        delay_constant = model.constants[rtol_element_name_to_use]
        adf_sm.equation = _apply_delay_with_offset(model, delayed_conv, delay_constant)
        elements[adf_sm_name] = adf_sm
        sector_delivery_converters.append(adf_sm)

    # Anchor_Delivery_Flow_<m> = sum_s Anchor_Delivery_Flow_<s>_<m>
    adf_m_name = anchor_delivery_flow_product(material)
    adf_m = model.converter(adf_m_name)
    if not sector_delivery_converters:
        adf_m.equation = 0.0
    else:
        expr = sector_delivery_converters[0]
        for sconv in sector_delivery_converters[1:]:
            expr = expr + sconv
        adf_m.equation = expr
    elements[adf_m_name] = adf_m


def _build_sector_blocks(model: Model, bundle: Phase1Bundle, elements: Dict[str, object]) -> None:
    """Create sector-level constants and agent-creation signals for all sectors."""
    _build_anchor_constants(model, bundle, elements)
    for sector in bundle.lists.sectors:
        if sector not in bundle.anchor.by_sector.columns:
            continue
        _build_sector_agent_creation_block(model, bundle, sector, elements)


def _build_sm_blocks(model: Model, bundle: Phase1Bundle, elements: Dict[str, object]) -> None:
    """Create SM-mode per-(s,m) creation pipelines for all pairs in `lists_sm`.

    Preconditions: `lists_sm` non-empty and `anchor_sm` contains full coverage per 17.1.
    """
    sm_df = getattr(bundle, "lists_sm", None)
    if sm_df is None or sm_df.empty:
        raise ValueError("SM-mode build requested but lists_sm is empty or missing")
    # Create blocks for each pair
    for _, row in sm_df.iterrows():
        sector = str(row["Sector"])
        material = str(row["Material"])
        _build_sm_agent_creation_block(model, bundle, sector, material, elements)


def build_phase4_model(bundle: Phase1Bundle, runspecs: RunSpecs) -> Phase4BuildResult:
    """Build the Phase 4 SD model for direct clients and lookups.

    Parameters
    - bundle: Phase 1 validated inputs (lists, params, tables)
    - runspecs: start, stop, dt settings (quarters for delays; years for time axis)

    Returns: Phase4BuildResult containing the configured BPTK_Py model.
    """
    model = Model()
    # Set run specs directly on model
    model.starttime = float(runspecs.starttime)
    model.stoptime = float(runspecs.stoptime)
    model.dt = float(runspecs.dt)

    elements: Dict[str, object] = {}

    # Create per-material structures
    for material in bundle.lists.products:
        _build_product_block(model, bundle, material, elements, anchor_mode=getattr(runspecs, "anchor_mode", "sector"))

    # Create agent creation signals depending on anchor mode
    if getattr(runspecs, "anchor_mode", "sector") == "sm":
        # Exclusivity: do not build sector-level creation in SM-mode
        _build_sm_blocks(model, bundle, elements)
    else:
        _build_sector_blocks(model, bundle, elements)

    return Phase4BuildResult(model=model, elements=elements)


def apply_scenario_overrides(model: Model, scenario: Scenario) -> None:
    """Apply scenario overrides to constants and lookup points.

    - For constants: set the element's equation to the override value.
    - For points: reassign the lookup converter's equation with the new points.
    """
    # Apply constants
    for const_name, value in scenario.constants.items():
        # Use model-internal registry instead of attribute access
        const_map = getattr(model, "constants", {})
        if const_name not in const_map:
            raise ValueError(f"Scenario constant '{const_name}' not found in model elements; check naming alignment")
        const_map[const_name].equation = float(value)

    # Apply lookup points
    for lookup_name, points in scenario.points.items():
        # Determine corresponding converter name
        if lookup_name.startswith("price_"):
            material = lookup_name[len("price_"):].replace("_", " ")
            conv_name = price_converter_product(material)
            scale = 1.0
        elif lookup_name.startswith("max_capacity_"):
            material = lookup_name[len("max_capacity_"):].replace("_", " ")
            conv_name = max_capacity_converter_product(material)
            # Capacity points are specified per year; model uses per-quarter. Preserve the build-time /4 scaling.
            scale = 0.25
        else:
            raise ValueError(f"Unknown lookup override key '{lookup_name}'")

        conv_map = getattr(model, "converters", {})
        if conv_name not in conv_map:
            raise ValueError(f"Lookup converter '{conv_name}' for override '{lookup_name}' not found in model")
        normalized = [(float(t), float(v)) for (t, v) in points]
        conv_map[conv_name].equation = F.lookup(F.time(), normalized) * scale
        # Update lookup meta for Phase 15 warnings/extrapolation awareness
        meta = getattr(model, "_lookup_points_meta", None)
        if meta is None:
            meta = {}
            setattr(model, "_lookup_points_meta", meta)
        meta[conv_name] = {
            "points": normalized,
            "tmin": min(p[0] for p in normalized) if normalized else None,
            "tmax": max(p[0] for p in normalized) if normalized else None,
            "kind": "capacity" if lookup_name.startswith("max_capacity_") else "price",
        }


__all__ = [
    "Phase4BuildResult",
    "build_phase4_model",
    "apply_scenario_overrides",
]
