from __future__ import annotations

"""
Phase 2 — Element Naming Utilities

This module provides deterministic, collision-safe helpers for generating
canonical element names used throughout the SD+ABM model and scenario overrides.

Design goals:
- Normalize human-readable labels (base/sector/material) to BPTK-compatible
  names using underscores for spaces and safe characters only.
- Preserve readability and case of the provided base label; only sanitize
  illegal characters and whitespace.
- Enforce a generous maximum length and apply a stable hash-based suffix when
  truncation is necessary to avoid excessively long names.
- Optionally track registrations to detect unintended name collisions.

Notes:
- We intentionally do not lowercase the base string to keep element names
  matching the architecture (e.g., "Anchor_Lead_Generation_<sector>").
- Scenario constants follow snake_case bases (e.g., "anchor_lead_generation_rate_<sector>").
"""

from dataclasses import dataclass
import hashlib
import re
from typing import Dict, Optional, Tuple


DEFAULT_MAX_NAME_LENGTH = 100  # generous limit; truncation is rare


def _normalize_component(raw: str) -> str:
    """Normalize a single name component to contain only safe characters.

    Rules:
    - Strip leading/trailing whitespace
    - Replace any run of non-alphanumeric characters with a single underscore
    - Collapse multiple underscores to one
    - Strip leading/trailing underscores

    Case is preserved to honor explicit names from the architecture.
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    # Replace groups of non-alphanumeric with underscore
    s = re.sub(r"[^0-9A-Za-z]+", "_", s)
    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s)
    # Trim underscores
    s = s.strip("_")
    return s


def _stable_suffix_hash(parts: Tuple[str, ...], length: int = 8) -> str:
    """Return a short, stable hex hash for the provided parts.

    Uses SHA1 over the exact tuple contents for reproducibility.
    """
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")  # separator to avoid concatenation ambiguities
    return h.hexdigest()[:length]


@dataclass
class NameRegistry:
    """Optional registry to detect unintended name collisions.

    The registry maps final element names to the source triple used to create
    them. Registering the same final name with different inputs raises.
    """

    final_to_source: Dict[str, Tuple[str, Optional[str], Optional[str]]] = None

    def __post_init__(self) -> None:
        if self.final_to_source is None:
            self.final_to_source = {}

    def register(self, final_name: str, source: Tuple[str, Optional[str], Optional[str]]) -> None:
        existing = self.final_to_source.get(final_name)
        if existing is None:
            self.final_to_source[final_name] = source
            return
        if existing != source:
            raise ValueError(
                "Name collision detected: final name '{final}' already registered for "
                "source={src1}, attempted source={src2}".format(
                    final=final_name, src1=existing, src2=source
                )
            )


def create_element_name(
    base: str,
    sector: Optional[str] = None,
    material: Optional[str] = None,
    *,
    max_length: int = DEFAULT_MAX_NAME_LENGTH,
    registry: Optional[NameRegistry] = None,
) -> str:
    """Create a canonical element name, normalized and collision-safe.

    Parameters
    ----------
    base : str
        The base label, e.g., "Anchor_Lead_Generation" or
        "anchor_lead_generation_rate" (case is preserved).
    sector : Optional[str]
        The sector label to append as a component.
    material : Optional[str]
        The material label to append as a component.
    max_length : int
        Maximum allowed length for the final name (default ~100 chars).
    registry : Optional[NameRegistry]
        If provided, registers the final name against the (base, sector, material)
        triple and raises on collision with a different triple.

    Returns
    -------
    str
        The canonical element name.
    """

    # Normalize components independently to keep intent clear
    norm_base = _normalize_component(base)
    norm_sector = _normalize_component(sector) if sector else ""
    norm_material = _normalize_component(material) if material else ""

    # Compose with underscores, skipping empty components
    components = [x for x in (norm_base, norm_sector, norm_material) if x]
    preliminary = "_".join(components)

    if len(preliminary) <= max_length:
        final_name = preliminary
    else:
        # Append a stable, short hash to preserve uniqueness while truncating
        suffix = _stable_suffix_hash((norm_base, norm_sector, norm_material))
        # Leave space for '_' + suffix
        allowed = max(1, max_length - (len(suffix) + 1))
        truncated = preliminary[:allowed].rstrip("_")
        final_name = f"{truncated}_{suffix}"

    if registry is not None:
        registry.register(final_name, (norm_base, norm_sector or None, norm_material or None))

    return final_name


# ---- Canonical helper functions (match technical_architecture.md) ----

# Constants (scenario overrides, SD constants)
def anchor_constant(param: str, sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name(param, sector, None, registry=registry)


def other_constant(param: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name(param, None, material, registry=registry)


def anchor_constant_sm(param: str, sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Per-(sector, material) anchor constant name helper.

    Example: requirement_to_order_lag_Defense_Silicon_Carbide_Fiber
    """
    return create_element_name(param, sector, material, registry=registry)


# Lookup table names (raw lookup identifiers)
def price_lookup_name(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("price", None, material, registry=registry)


def max_capacity_lookup_name(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("max_capacity", None, material, registry=registry)


# Converter names for lookups at time t
def price_converter(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Price", None, material, registry=registry)


def max_capacity_converter(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("max_capacity_lookup", None, material, registry=registry)


# Sector-level SD elements
def anchor_lead_generation(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Anchor_Lead_Generation", sector, None, registry=registry)


def cpc_stock(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("CPC", sector, None, registry=registry)


def new_pc_flow(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("New_PC_Flow", sector, None, registry=registry)


def agent_creation_accumulator(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Agent_Creation_Accumulator", sector, None, registry=registry)


def agent_creation_inflow(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Agent_Creation_Inflow", sector, None, registry=registry)


def agent_creation_outflow(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Agent_Creation_Outflow", sector, None, registry=registry)


def agents_to_create_converter(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Agents_To_Create", sector, None, registry=registry)


def cumulative_agents_created(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Cumulative_Agents_Created", sector, None, registry=registry)


def cumulative_inflow(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Cumulative_Inflow", sector, None, registry=registry)


def agent_creation_trigger(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Agent_Creation_Trigger", sector, None, registry=registry)


# Material-level SD elements (direct clients)
def inbound_leads(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Inbound_Leads", None, material, registry=registry)


def outbound_leads(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Outbound_Leads", None, material, registry=registry)


def total_new_leads(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Total_New_Leads", None, material, registry=registry)


def potential_clients_stock(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Potential_Clients", None, material, registry=registry)


def client_creation_flow(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Client_Creation", None, material, registry=registry)


def c_stock(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    # Capital C as in architecture: C_<m>
    return create_element_name("C", None, material, registry=registry)


def avg_order_quantity(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("avg_order_quantity", None, material, registry=registry)


def client_requirement(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Client_Requirement", None, material, registry=registry)


def fulfillment_ratio(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Fulfillment_Ratio", None, material, registry=registry)


def delayed_client_demand(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Delayed_Client_Demand", None, material, registry=registry)


def client_delivery_flow(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Client_Delivery_Flow", None, material, registry=registry)


def client_revenue(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Client_Revenue", None, material, registry=registry)


# ABM→SD Gateway and anchor deliveries
def agent_demand_sector_input(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Agent_Demand_Sector_Input", sector, material, registry=registry)


def agent_aggregated_demand(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Agent_Aggregated_Demand", None, material, registry=registry)


def total_demand(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Total_Demand", None, material, registry=registry)


def delayed_agent_demand(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Delayed_Agent_Demand", sector, material, registry=registry)


def anchor_delivery_flow_sector_material(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Anchor_Delivery_Flow", sector, material, registry=registry)


def anchor_delivery_flow_material(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Anchor_Delivery_Flow", None, material, registry=registry)


def anchor_revenue_sector_material(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Anchor_Revenue", sector, material, registry=registry)


def anchor_revenue_sector(sector: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Anchor_Revenue", sector, None, registry=registry)


def anchor_revenue_material(material: str, *, registry: Optional[NameRegistry] = None) -> str:
    return create_element_name("Anchor_Revenue", None, material, registry=registry)


def total_revenue(*, registry: Optional[NameRegistry] = None) -> str:
    # No sector/material component
    return create_element_name("Total_Revenue", None, None, registry=registry)


# ---- SM-mode (sector, material) creation signal helpers (Phase 17.2) ----
def anchor_lead_generation_sm(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Canonical name for per-(sector, material) lead-generation converter in SM-mode."""
    return create_element_name("Anchor_Lead_Generation", sector, material, registry=registry)


def cpc_stock_sm(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Canonical name for per-(sector, material) CPC stock that integrates anchor leads in SM-mode."""
    return create_element_name("CPC", sector, material, registry=registry)


def new_pc_flow_sm(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Canonical name for per-(sector, material) New_PC_Flow converter in SM-mode."""
    return create_element_name("New_PC_Flow", sector, material, registry=registry)


def agent_creation_accumulator_sm(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Canonical name for per-(sector, material) Agent_Creation_Accumulator stock in SM-mode."""
    return create_element_name("Agent_Creation_Accumulator", sector, material, registry=registry)


def agent_creation_inflow_sm(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Canonical name for per-(sector, material) Agent_Creation_Inflow converter in SM-mode."""
    return create_element_name("Agent_Creation_Inflow", sector, material, registry=registry)


def agent_creation_outflow_sm(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Canonical name for per-(sector, material) Agent_Creation_Outflow converter (integerize via floor-like round) in SM-mode."""
    return create_element_name("Agent_Creation_Outflow", sector, material, registry=registry)


def agents_to_create_converter_sm(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Canonical name for per-(sector, material) Agents_To_Create converter (integer creations this step) in SM-mode."""
    return create_element_name("Agents_To_Create", sector, material, registry=registry)


def cumulative_inflow_sm(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Canonical name for per-(sector, material) Cumulative_Inflow converter feeding the cumulative created stock in SM-mode."""
    return create_element_name("Cumulative_Inflow", sector, material, registry=registry)


def cumulative_agents_created_sm(sector: str, material: str, *, registry: Optional[NameRegistry] = None) -> str:
    """Canonical name for per-(sector, material) Cumulative_Agents_Created stock in SM-mode."""
    return create_element_name("Cumulative_Agents_Created", sector, material, registry=registry)


__all__ = [
    # Core API
    "NameRegistry",
    "create_element_name",
    # Constants helpers
    "anchor_constant",
    "anchor_constant_sm",
    "other_constant",
    # Lookup helpers
    "price_lookup_name",
    "max_capacity_lookup_name",
    "price_converter",
    "max_capacity_converter",
    # Sector helpers
    "anchor_lead_generation",
    "cpc_stock",
    "new_pc_flow",
    "agent_creation_accumulator",
    "agent_creation_inflow",
    "agent_creation_outflow",
    "agents_to_create_converter",
    "cumulative_agents_created",
    "cumulative_inflow",
    "agent_creation_trigger",
    # Material helpers
    "inbound_leads",
    "outbound_leads",
    "total_new_leads",
    "potential_clients_stock",
    "client_creation_flow",
    "c_stock",
    "avg_order_quantity",
    "client_requirement",
    "fulfillment_ratio",
    "delayed_client_demand",
    "client_delivery_flow",
    "client_revenue",
    # Gateways and deliveries
    "agent_demand_sector_input",
    "agent_aggregated_demand",
    "total_demand",
    "delayed_agent_demand",
    "anchor_delivery_flow_sector_material",
    "anchor_delivery_flow_material",
    "anchor_revenue_sector_material",
    "anchor_revenue_sector",
    "anchor_revenue_material",
    "total_revenue",
    # SM-mode creation helpers
    "anchor_lead_generation_sm",
    "cpc_stock_sm",
    "new_pc_flow_sm",
    "agent_creation_accumulator_sm",
    "agent_creation_inflow_sm",
    "agent_creation_outflow_sm",
    "agents_to_create_converter_sm",
    "cumulative_inflow_sm",
    "cumulative_agents_created_sm",
]


