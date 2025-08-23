"""Growth System source package.

Exports Phase 2 naming utilities for convenient imports.

Note: Phase 12 introduces a `viz` subpackage used only by the CLI runner
with the `--visualize` flag. The visualization components are imported
at runtime by `simulate_growth.py` to avoid adding optional
dependencies to module import time.
"""

from .naming import (
    anchor_constant,
    anchor_constant_sm,
    product_constant,
    price_lookup_name_product,
    max_capacity_lookup_name_product,
    price_converter_product,
    max_capacity_converter_product,
    agent_aggregated_demand,
    agent_demand_sector_input,
    total_demand,
    fulfillment_ratio,
    delayed_client_demand,
    client_delivery_flow,
    client_revenue,
    anchor_delivery_flow_product,
    anchor_delivery_flow_sector_product,
    anchor_lead_generation,
    cpc_stock,
    new_pc_flow,
    agent_creation_accumulator,
    agent_creation_inflow,
    agent_creation_outflow,
    agents_to_create_converter,
    cumulative_agents_created,
    cumulative_inflow,
    anchor_lead_generation_sm,
    cpc_stock_sm,
    new_pc_flow_sm,
    agent_creation_accumulator_sm,
    agent_creation_inflow_sm,
    agent_creation_outflow_sm,
    agents_to_create_converter_sm,
    cumulative_agents_created_sm,
    cumulative_inflow_sm,
    anchor_revenue_sector,
    anchor_revenue_sector_product,
    anchor_revenue_product,
)

# Explicitly expose the naming API when users do `from src import *`.
__all__ = [
    "anchor_constant",
    "anchor_constant_sm",
    "product_constant",
    "price_lookup_name_product",
    "max_capacity_lookup_name_product",
    "price_converter_product",
    "max_capacity_converter_product",
    "agent_aggregated_demand",
    "agent_demand_sector_input",
    "total_demand",
    "fulfillment_ratio",
    "delayed_client_demand",
    "client_delivery_flow",
    "client_revenue",
    "anchor_delivery_flow_product",
    "anchor_delivery_flow_sector_product",
    "anchor_lead_generation",
    "cpc_stock",
    "new_pc_flow",
    "agent_creation_accumulator",
    "agent_creation_inflow",
    "agent_creation_outflow",
    "agents_to_create_converter",
    "cumulative_agents_created",
    "cumulative_inflow",
    "anchor_lead_generation_sm",
    "cpc_stock_sm",
    "new_pc_flow_sm",
    "agent_creation_accumulator_sm",
    "agent_creation_inflow_sm",
    "agent_creation_outflow_sm",
    "agents_to_create_converter_sm",
    "cumulative_agents_created_sm",
    "cumulative_inflow_sm",
    "anchor_revenue_sector",
    "anchor_revenue_sector_product",
    "anchor_revenue_product",
]

# Phase 5 ABM agents
from .abm_anchor import (  # noqa: F401
    AnchorClientAgentState,
    AnchorClientParams,
    AnchorClientAgent,
    build_anchor_agent_factory_for_sector,
    build_all_anchor_agent_factories,
)

# Extend exported API
__all__ += [
    "AnchorClientAgentState",
    "AnchorClientParams",
    "AnchorClientAgent",
    "build_anchor_agent_factory_for_sector",
    "build_all_anchor_agent_factories",
]
