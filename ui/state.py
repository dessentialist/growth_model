from __future__ import annotations

"""
Typed UI state models for the Streamlit GUI.

This module defines minimal, decoupled dataclasses that hold the current UI
scenario being edited: runspecs, constants overrides, and points (lookup) overrides.

The functions in this module are pure helpers for translating UI state to a
scenario dict compatible with `src.scenario_loader.validate_scenario_dict`.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional


@dataclass
class RunspecsState:
    """Runspecs fields with safe defaults.

    - starttime, stoptime, and dt are floats in year units
    - anchor_mode controls sector vs SM behavior. For Phases 3–5 we default to
      'sector' and allow switching to 'sm' to preview permissible keys.
    """

    starttime: float = 2025.0
    stoptime: float = 2032.0
    dt: float = 0.25
    anchor_mode: str = "sector"


@dataclass
class SimulationDefinitionsState:
    """Holds the market, sector, and product lists for simulation configuration.
    
    These lists define the universe of markets, sectors, and products that can
    be used in the simulation. They are editable through the UI and must be
    saved before changes take effect.
    """
    
    markets: List[str] = field(default_factory=lambda: ["Market_1", "Market_2"])
    sectors: List[str] = field(default_factory=lambda: ["Sector_1", "Sector_2", "Sector_3", "Sector_4"])
    products: List[str] = field(default_factory=lambda: ["Product_1", "Product_2", "Product_3", "Product_4", "Product_5", "Product_6", "Product_7", "Product_8"])
    
    # Track unsaved changes for save button functionality
    has_unsaved_changes: bool = False


@dataclass
class ClientRevenueState:
    """Holds client revenue parameters organized by sector-product combinations.
    
    This state manages the 19 parameters for client revenue across three groups:
    - Market Activation (9 parameters)
    - Orders (9 parameters) 
    - Seeds (3 parameters)
    
    Parameters are organized by sector-product combinations that are dynamically
    populated based on the primary mapping selections.
    """
    
    # Market Activation Parameters (9 total)
    market_activation_params: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Orders Parameters (9 total)  
    orders_params: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Seeds Parameters (3 total)
    seeds_params: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Track unsaved changes for save button functionality
    has_unsaved_changes: bool = False


@dataclass
class DirectMarketRevenueState:
    """Holds direct market revenue parameters organized by products.
    
    This state manages the 9 parameters for direct market revenue:
    - lead_start_year, inbound_lead_generation_rate, outbound_lead_generation_rate
    - lead_to_c_conversion_rate, lead_to_requirement_delay, requirement_to_fulfilment_delay
    - avg_order_quantity_initial, client_requirement_growth, TAM
    
    Parameters are organized by products (not sector-product combinations) since
    direct market revenue is product-specific, not sector-specific.
    """
    
    # Direct Market Revenue Parameters (9 total) - organized by product
    direct_market_params: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Track unsaved changes for save button functionality
    has_unsaved_changes: bool = False


@dataclass
class LookupPointsState:
    """Holds time-series lookup points for production capacity and pricing.
    
    This state manages:
    - Production capacity lookup tables (max_capacity_<product>)
    - Price lookup tables (price_<product>)
    
    Tables are organized with years as columns and products as rows.
    """
    
    # Production capacity lookup tables per product per year
    production_capacity: Dict[str, Dict[float, float]] = field(default_factory=dict)
    
    # Price lookup tables per product per year
    pricing: Dict[str, Dict[float, float]] = field(default_factory=dict)
    
    # Track unsaved changes for save button functionality
    has_unsaved_changes: bool = False


@dataclass
class RunnerState:
    """Holds runner execution state and configuration.
    
    This state manages scenario execution controls, monitoring, and status.
    """
    
    # Execution status
    is_running: bool = False
    current_scenario: Optional[str] = None
    
    # Execution settings
    debug_mode: bool = False
    generate_plots: bool = False
    kpi_sm_revenue_rows: bool = False
    kpi_sm_client_rows: bool = False
    
    # Track unsaved changes for save button functionality
    has_unsaved_changes: bool = False


@dataclass
class LogsState:
    """Holds logs configuration and display state.
    
    This state manages simulation logs display, filtering, and export.
    """
    
    # Log display settings
    log_level: str = "INFO"
    max_log_lines: int = 1000
    auto_refresh: bool = True
    
    # Track unsaved changes for save button functionality
    has_unsaved_changes: bool = False


@dataclass
class ScenarioOverridesState:
    """Holds override maps for constants and points (lookups).

    - constants: mapping of element name -> numeric value
    - points: mapping of lookup name -> list of [time, value] numeric pairs
    """

    constants: Dict[str, float] = field(default_factory=dict)
    points: Dict[str, List[Tuple[float, float]]] = field(default_factory=dict)


@dataclass
class PrimaryMapEntry:
    """Represents a proposed mapping of a single product to a sector with a start year.

    The UI captures proposed replacements to the primary product map on a per-sector basis.
    Each entry pairs a `product` with its `start_year`.
    """

    product: str
    start_year: float


@dataclass
class PrimaryMapState:
    """Holds proposed primary map replacements per sector.

    Structure mirrors the scenario schema expected by the backend validator:
    overrides.primary_map: { <sector>: [ { product: <str>, start_year: <float> }, ... ] }
    """

    by_sector: Dict[str, List[PrimaryMapEntry]] = field(default_factory=dict)


@dataclass
class SeedsState:
    """Holds seeding configuration for the scenario.

    - active_anchor_clients: number of ACTIVE anchor agents at t0 per sector
    - elapsed_quarters: optional aging per sector in quarters
    - direct_clients: number of direct clients per product at t0
    - active_anchor_clients_sm: SM-mode seeds per (sector, product)
    - elapsed_quarters_sm: SM-mode aging per (sector, product) in quarters
    - completed_projects: sector-mode backlog of completed projects at t0
    - completed_projects_sm: SM-mode backlog per (sector, product)
    """

    active_anchor_clients: Dict[str, int] = field(default_factory=dict)
    elapsed_quarters: Dict[str, int] = field(default_factory=dict)
    direct_clients: Dict[str, int] = field(default_factory=dict)
    active_anchor_clients_sm: Dict[str, Dict[str, int]] = field(default_factory=dict)
    elapsed_quarters_sm: Dict[str, Dict[str, int]] = field(default_factory=dict)
    completed_projects: Dict[str, int] = field(default_factory=dict)
    completed_projects_sm: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class UIState:
    """Aggregate UI state for the scenario under construction."""

    name: str = "working_scenario"
    runspecs: RunspecsState = field(default_factory=RunspecsState)
    simulation_definitions: SimulationDefinitionsState = field(default_factory=SimulationDefinitionsState)
    overrides: ScenarioOverridesState = field(default_factory=ScenarioOverridesState)
    primary_map: PrimaryMapState = field(default_factory=PrimaryMapState)
    client_revenue: ClientRevenueState = field(default_factory=ClientRevenueState)
    direct_market_revenue: DirectMarketRevenueState = field(default_factory=DirectMarketRevenueState)
    lookup_points: LookupPointsState = field(default_factory=LookupPointsState)
    seeds: SeedsState = field(default_factory=SeedsState)
    runner: RunnerState = field(default_factory=RunnerState)
    logs: LogsState = field(default_factory=LogsState)
    # Track previously loaded lists_sm (if any) to inform save-time decisions in SM mode
    previous_lists_sm: List[Tuple[str, str]] = field(default_factory=list)
    # Snapshots of last-saved scenario values for Reset functionality
    last_saved_constants: Dict[str, float] = field(default_factory=dict)
    last_saved_points: Dict[str, List[Tuple[float, float]]] = field(default_factory=dict)
    # Seeds snapshot for Reset functionality
    last_saved_seeds: Dict[str, dict] = field(default_factory=dict)

    def to_scenario_dict(self) -> dict:
        """Translate to a plain dict expected by scenario validation.

        For Phases 6–8, we include runspecs, overrides (constants, points, primary_map)
        and seeds blocks. Points are returned as-is (may contain tuples), while
        `to_scenario_dict_normalized` ensures lists for serialization.
        """
        # Always snapshot primary_map for all sectors to mirror UI exactly
        pm_block: Dict[str, List[Dict[str, float]]] = {}
        sectors: List[str] = list(self.simulation_definitions.sectors)
        for sector in sectors:
            entries = self.primary_map.by_sector.get(sector, [])
            pm_block[sector] = [{"product": e.product, "start_year": float(e.start_year)} for e in entries]

        seeds_block: Optional[dict] = None
        if (
            self.seeds.active_anchor_clients
            or self.seeds.elapsed_quarters
            or self.seeds.direct_clients
            or self.seeds.active_anchor_clients_sm
            or self.seeds.elapsed_quarters_sm
            or self.seeds.completed_projects
            or self.seeds.completed_projects_sm
        ):
            seeds_block = {}
            if self.seeds.active_anchor_clients:
                seeds_block["active_anchor_clients"] = dict(self.seeds.active_anchor_clients)
            if self.seeds.elapsed_quarters:
                seeds_block["elapsed_quarters"] = dict(self.seeds.elapsed_quarters)
            if self.seeds.direct_clients:
                seeds_block["direct_clients"] = dict(self.seeds.direct_clients)
            if self.seeds.active_anchor_clients_sm:
                seeds_block["active_anchor_clients_sm"] = {
                    s: dict(mmap) for s, mmap in self.seeds.active_anchor_clients_sm.items()
                }
            if self.seeds.elapsed_quarters_sm:
                seeds_block["elapsed_quarters_sm"] = {
                    s: dict(mmap) for s, mmap in self.seeds.elapsed_quarters_sm.items()
                }
            if self.seeds.completed_projects:
                seeds_block["completed_projects"] = dict(self.seeds.completed_projects)
            if self.seeds.completed_projects_sm:
                seeds_block["completed_projects_sm"] = {s: dict(mmap) for s, mmap in self.seeds.completed_projects_sm.items()}

        # Convert direct market revenue parameters to scenario constants
        direct_market_constants = self._convert_direct_market_params_to_constants()
        # Convert client revenue parameters to scenario constants
        client_revenue_constants = self._convert_client_revenue_params_to_constants()
        
        # Merge all constants (existing overrides + direct market revenue)
        all_constants = dict(self.overrides.constants)
        all_constants.update(direct_market_constants)
        all_constants.update(client_revenue_constants)
        
        overrides_block: dict = {
            "constants": all_constants,
            "primary_map": pm_block,
            # Points omitted here; use normalized variant for serialization
        }

        out: dict = {
            "name": self.name,
            "runspecs": asdict(self.runspecs),
            "overrides": overrides_block,
        }
        # In SM mode, auto-sync lists_sm from current primary mapping for a faithful SP universe
        if str(self.runspecs.anchor_mode).strip().lower() == "sm":
            out["lists_sm"] = self._derive_lists_sm_from_primary_map()
        if seeds_block:
            out["seeds"] = seeds_block
        return out

    def to_scenario_dict_normalized(self) -> dict:
        """Assemble a scenario dict with normalized points as lists, not tuples."""
        points_map: Dict[str, List[List[float]]] = {}
        for name, series in self.overrides.points.items():
            # Ensure list-of-lists shape for YAML/JSON dumps and validation
            points_map[name] = [[float(t), float(v)] for (t, v) in series]
        # Start from non-normalized dict to include optional blocks
        base = self.to_scenario_dict()
        overrides_block = dict(base.get("overrides", {}))
        overrides_block["points"] = points_map
        base["overrides"] = overrides_block
        return base

    def _convert_direct_market_params_to_constants(self) -> Dict[str, float]:
        """Convert direct market revenue parameters to scenario constants.
        
        Converts product-level parameters to the format expected by the model:
        - lead_start_year_<product>
        - inbound_lead_generation_rate_<product>
        - outbound_lead_generation_rate_<product>
        - lead_to_c_conversion_rate_<product>
        - lead_to_requirement_delay_<product>
        - requirement_to_fulfilment_delay_<product>
        - avg_order_quantity_initial_<product>
        - client_requirement_growth_<product>
        - requirement_limit_multiplier_<product>
        - TAM_<product>
        
        Returns:
            Dictionary mapping constant names to values
        """
        constants = {}
        
        for product, params in self.direct_market_revenue.direct_market_params.items():
            for param_name, value in params.items():
                # Create the constant name in the format expected by the model
                constant_name = f"{param_name}_{product}"
                constants[constant_name] = float(value)
        
        return constants

    def _convert_client_revenue_params_to_constants(self) -> Dict[str, float]:
        """Convert client revenue parameters (per sector-product) to constants.

        Follows the canonical naming scheme `<param>_<Sector>_<Product>` for
        all parameters across Market Activation and Orders groups.
        """
        constants: Dict[str, float] = {}
        for sp_key, params in self.client_revenue.market_activation_params.items():
            # sp_key format is "Sector_Product"
            for param_name, value in params.items():
                constants[f"{param_name}_{sp_key}"] = float(value)
        for sp_key, params in self.client_revenue.orders_params.items():
            for param_name, value in params.items():
                constants[f"{param_name}_{sp_key}"] = float(value)
        return constants

    def _derive_lists_sm_from_primary_map(self) -> List[Dict[str, str]]:
        """Derive lists_sm as a list of {Sector, Material} pairs from current primary map.

        Returns:
            List of dictionaries with keys 'Sector' and 'Material'.
        """
        pairs: List[Dict[str, str]] = []
        for sector, entries in self.primary_map.by_sector.items():
            for e in entries:
                pairs.append({"Sector": sector, "Material": e.product})
        # Ensure deterministic order
        pairs.sort(key=lambda d: (d["Sector"], d["Material"]))
        return pairs

    def load_from_scenario_dict(self, data: dict, bundle=None) -> None:
        """Load state from a scenario dict produced by loader or YAML.

        This function mutates the current instance to reflect the provided
        scenario. Unknown fields are ignored; missing fields retain defaults.
        
        Args:
            data: Scenario dictionary from YAML/JSON
            bundle: Optional Phase1Bundle to load simulation definitions from
        """
        if not isinstance(data, dict):
            return
        # Name
        self.name = str(data.get("name") or self.name)
        # Runspecs
        rs = data.get("runspecs") or {}
        try:
            self.runspecs.starttime = float(rs.get("starttime", self.runspecs.starttime))
            self.runspecs.stoptime = float(rs.get("stoptime", self.runspecs.stoptime))
            self.runspecs.dt = float(rs.get("dt", self.runspecs.dt))
            mode = str(rs.get("anchor_mode", self.runspecs.anchor_mode)).strip().lower()
            if mode in {"sector", "sm"}:
                self.runspecs.anchor_mode = mode
            # Mark that runspecs were loaded from scenario
            self.runspecs._loaded_from_scenario = True
        except Exception:
            pass
        
        # Load simulation definitions from bundle if available
        if bundle is not None:
            self._load_simulation_definitions_from_bundle(bundle)
            # Load primary mapping from bundle first
            self._load_primary_mapping_from_bundle(bundle)
            # Load runspecs defaults from bundle
            self._load_runspecs_defaults_from_bundle(bundle)
        
        # Overrides.constants
        ov = data.get("overrides") or {}
        consts = ov.get("constants") or {}
        if isinstance(consts, dict):
            self.overrides.constants = {str(k): float(v) for k, v in consts.items()}
            # Map constants to UI state components
            self._map_constants_to_ui_state(consts)
            # Snapshot last-saved constants
            self.last_saved_constants = {str(k): float(v) for k, v in consts.items()}
        
        # Initialize client revenue state with proper defaults after loading constants
        if bundle is not None:
            self._initialize_client_revenue_state_from_bundle(bundle)
        # Overrides.points
        points = ov.get("points") or {}
        if isinstance(points, dict):
            norm_points: Dict[str, List[Tuple[float, float]]] = {}
            for name, series in points.items():
                rows: List[Tuple[float, float]] = []
                if isinstance(series, list):
                    for pair in series:
                        if isinstance(pair, (list, tuple)) and len(pair) == 2:
                            try:
                                rows.append((float(pair[0]), float(pair[1])))
                            except Exception:
                                continue
                if rows:
                    rows.sort(key=lambda x: x[0])
                    norm_points[str(name)] = rows
            self.overrides.points = norm_points
            # Snapshot last-saved points
            self.last_saved_points = {str(k): list(v) for k, v in norm_points.items()}
        # Overrides.primary_map
        pm = ov.get("primary_map") or {}
        if isinstance(pm, dict) and pm is not None:
            # Replace semantics: sectors listed in primary_map are replaced entirely
            # by the provided list, including the case of an empty list (clear sector mapping).
            by_sector_overrides: Dict[str, List[PrimaryMapEntry]] = {}
            for s, entries in pm.items():
                if isinstance(entries, list):
                    ll: List[PrimaryMapEntry] = []
                    for e in entries:
                        if isinstance(e, dict):
                            prod = str(e.get("product", "")).strip()
                            sy = e.get("start_year", 2025.0)
                            try:
                                syf = float(sy)
                            except Exception:
                                syf = 2025.0
                            if prod:
                                ll.append(PrimaryMapEntry(product=prod, start_year=syf))
                    # Assign even if ll is empty to clear mapping for the sector
                    by_sector_overrides[str(s)] = sorted(ll, key=lambda x: x.product)
            # Apply sector replacements
            for sector, entries in by_sector_overrides.items():
                self.primary_map.by_sector[sector] = entries
        # Scenario-level lists_sm (if present) — capture for SM-mode sync decisions
        raw_lists_sm = data.get("lists_sm")
        self.previous_lists_sm = []
        if isinstance(raw_lists_sm, (list, tuple)):
            for entry in raw_lists_sm:
                if isinstance(entry, dict):
                    s = str(entry.get("Sector", "")).strip()
                    m = str(entry.get("Material", "")).strip()
                    if s and m:
                        self.previous_lists_sm.append((s, m))
        # Ensure deterministic ordering for comparisons
        self.previous_lists_sm.sort(key=lambda x: (x[0], x[1]))
        # Seeds
        seeds = data.get("seeds") or {}
        if isinstance(seeds, dict):
            aac = seeds.get("active_anchor_clients") or {}
            if isinstance(aac, dict):
                self.seeds.active_anchor_clients = {str(k): int(v) for k, v in aac.items() if int(v) > 0}
            eq = seeds.get("elapsed_quarters") or {}
            if isinstance(eq, dict):
                self.seeds.elapsed_quarters = {str(k): int(v) for k, v in eq.items() if int(v) > 0}
            dc = seeds.get("direct_clients") or {}
            if isinstance(dc, dict):
                self.seeds.direct_clients = {str(k): int(v) for k, v in dc.items() if int(v) > 0}
            sm = seeds.get("active_anchor_clients_sm") or {}
            if isinstance(sm, dict):
                norm_sm: Dict[str, Dict[str, int]] = {}
                for s, mmap in sm.items():
                    if isinstance(mmap, dict):
                        mm = {str(m): int(v) for m, v in mmap.items() if int(v) > 0}
                        if mm:
                            norm_sm[str(s)] = mm
                self.seeds.active_anchor_clients_sm = norm_sm
            eqsm = seeds.get("elapsed_quarters_sm") or {}
            if isinstance(eqsm, dict):
                norm_eqsm: Dict[str, Dict[str, int]] = {}
                for s, mmap in eqsm.items():
                    if isinstance(mmap, dict):
                        mm = {str(m): int(v) for m, v in mmap.items() if int(v) > 0}
                        if mm:
                            norm_eqsm[str(s)] = mm
                self.seeds.elapsed_quarters_sm = norm_eqsm
            cp = seeds.get("completed_projects") or {}
            if isinstance(cp, dict):
                self.seeds.completed_projects = {str(k): int(v) for k, v in cp.items() if int(v) > 0}
            cpsm = seeds.get("completed_projects_sm") or {}
            if isinstance(cpsm, dict):
                norm_cpsm: Dict[str, Dict[str, int]] = {}
                for s, mmap in cpsm.items():
                    if isinstance(mmap, dict):
                        mm = {str(m): int(v) for m, v in mmap.items() if int(v) > 0}
                        if mm:
                            norm_cpsm[str(s)] = mm
                self.seeds.completed_projects_sm = norm_cpsm
        # Snapshot last-saved seeds from loaded scenario
        self.last_saved_seeds = {
            "active_anchor_clients": dict(self.seeds.active_anchor_clients),
            "elapsed_quarters": dict(self.seeds.elapsed_quarters),
            "direct_clients": dict(self.seeds.direct_clients),
            "active_anchor_clients_sm": {s: dict(m) for s, m in self.seeds.active_anchor_clients_sm.items()},
            "elapsed_quarters_sm": {s: dict(m) for s, m in self.seeds.elapsed_quarters_sm.items()},
            "completed_projects": dict(self.seeds.completed_projects),
            "completed_projects_sm": {s: dict(m) for s, m in self.seeds.completed_projects_sm.items()},
        }

    def _map_constants_to_ui_state(self, constants: Dict[str, float]) -> None:
        """Map scenario constants to UI state components.
        
        This method parses scenario constants and maps them to the appropriate
        UI state components (ClientRevenueState, DirectMarketRevenueState, etc.)
        based on the parameter naming conventions.
        
        Args:
            constants: Dictionary of constant name -> value mappings from scenario
        """
        # Define parameter mappings for client revenue parameters
        client_revenue_params = {
            # Market Activation Parameters
            'ATAM': 'ATAM',
            'anchor_start_year': 'anchor_start_year', 
            'anchor_lead_generation_rate': 'anchor_lead_generation_rate',
            'lead_to_pc_conversion_rate': 'lead_to_pc_conversion_rate',
            'project_generation_rate': 'project_generation_rate',
            'project_duration': 'project_duration',
            'projects_to_client_conversion': 'projects_to_client_conversion',
            'max_projects_per_pc': 'max_projects_per_pc',
            'anchor_client_activation_delay': 'anchor_client_activation_delay',
            
            # Orders Parameters
            'initial_phase_duration': 'initial_phase_duration',
            'initial_requirement_rate': 'initial_requirement_rate',
            'initial_req_growth': 'initial_req_growth',
            'ramp_phase_duration': 'ramp_phase_duration',
            'ramp_requirement_rate': 'ramp_requirement_rate',
            'ramp_req_growth': 'ramp_req_growth',
            'steady_requirement_rate': 'steady_requirement_rate',
            'steady_req_growth': 'steady_req_growth',
            'requirement_to_order_lag': 'requirement_to_order_lag',
            'ramp_requirement_rate_override': 'ramp_requirement_rate_override',
            'steady_requirement_rate_override': 'steady_requirement_rate_override',
        }
        
        # Define parameter mappings for direct market revenue parameters
        direct_market_params = {
            'lead_start_year': 'lead_start_year',
            'inbound_lead_generation_rate': 'inbound_lead_generation_rate',
            'outbound_lead_generation_rate': 'outbound_lead_generation_rate',
            'lead_to_c_conversion_rate': 'lead_to_c_conversion_rate',
            'lead_to_requirement_delay': 'lead_to_requirement_delay',
            'requirement_to_fulfilment_delay': 'requirement_to_fulfilment_delay',
            'avg_order_quantity_initial': 'avg_order_quantity_initial',
            'client_requirement_growth': 'client_requirement_growth',
            'requirement_limit_multiplier': 'requirement_limit_multiplier',  # NEW: Per-client order cap for cohort system
            'TAM': 'TAM',
        }
        
        # Get valid sector-product combinations from primary mapping
        valid_combinations = set()
        for sector, entries in self.primary_map.by_sector.items():
            for entry in entries:
                combination = f"{sector}_{entry.product}"
                valid_combinations.add(combination)
        
        # Process each constant
        for const_name, const_value in constants.items():
            # Parse sector-product combinations from constant names
            # Format: parameter_Sector_Product (e.g., initial_requirement_rate_Defense_Silicon_Carbide_Fiber)
            parts = const_name.split('_')
            if len(parts) >= 3:
                # Find the parameter name by matching against known parameters
                param_name = None
                sector_product = None
                
                # Try to match against client revenue parameters
                for param, ui_param in client_revenue_params.items():
                    if const_name.startswith(param + '_'):
                        param_name = ui_param
                        sector_product = '_'.join(parts[len(param.split('_')):])
                        break
                
                # If not found in client revenue, try direct market parameters
                if param_name is None:
                    for param, ui_param in direct_market_params.items():
                        if const_name.startswith(param + '_'):
                            param_name = ui_param
                            # For direct market parameters, extract just the product name (not sector-product)
                            # Format: parameter_Product (e.g., lead_start_year_Silicon_Carbide_Fiber)
                            product = '_'.join(parts[len(param.split('_')):])
                            break
                
                # Handle client revenue parameters (sector-product combinations)
                if param_name and param_name in client_revenue_params.values():
                    # Only map if the sector-product combination is valid (exists in primary mapping)
                    if sector_product and sector_product in valid_combinations:
                        if param_name in ['ATAM', 'anchor_start_year', 'anchor_lead_generation_rate', 
                                        'lead_to_pc_conversion_rate', 'project_generation_rate', 
                                        'project_duration', 'projects_to_client_conversion', 
                                        'max_projects_per_pc', 'anchor_client_activation_delay']:
                            # Market Activation Parameters
                            if sector_product not in self.client_revenue.market_activation_params:
                                self.client_revenue.market_activation_params[sector_product] = {}
                            self.client_revenue.market_activation_params[sector_product][param_name] = const_value
                        elif param_name in ['initial_phase_duration', 'initial_requirement_rate', 'initial_req_growth',
                                          'ramp_phase_duration', 'ramp_requirement_rate', 'ramp_req_growth',
                                          'steady_requirement_rate', 'steady_req_growth', 'requirement_to_order_lag',
                                          'ramp_requirement_rate_override', 'steady_requirement_rate_override']:
                            # Orders Parameters
                            if sector_product not in self.client_revenue.orders_params:
                                self.client_revenue.orders_params[sector_product] = {}
                            self.client_revenue.orders_params[sector_product][param_name] = const_value
                
                # Handle direct market revenue parameters (product-level only)
                elif param_name and param_name in direct_market_params.values():
                    # Map to direct market revenue state using product name only
                    if product:
                        if product not in self.direct_market_revenue.direct_market_params:
                            self.direct_market_revenue.direct_market_params[product] = {}
                        self.direct_market_revenue.direct_market_params[product][param_name] = const_value

    def _load_simulation_definitions_from_bundle(self, bundle) -> None:
        """Load simulation definitions (markets, sectors, products) from the bundle.
        
        Args:
            bundle: Phase1Bundle containing the simulation definitions
        """
        try:
            # Load markets from bundle - get all markets from the original data
            if hasattr(bundle, 'lists') and hasattr(bundle.lists, 'markets_sectors_materials'):
                # Get all unique markets from the bundle
                all_markets = bundle.lists.markets_sectors_materials["Market"].dropna().astype(str).str.strip().unique().tolist()
                if all_markets:
                    self.simulation_definitions.markets = all_markets
                else:
                    # Fallback to defaults if no markets found
                    self.simulation_definitions.markets = ["Market_1", "Market_2"]
            
            # Load sectors from bundle
            if hasattr(bundle, 'lists') and hasattr(bundle.lists, 'sectors'):
                self.simulation_definitions.sectors = bundle.lists.sectors
            
            # Load products from bundle
            if hasattr(bundle, 'lists') and hasattr(bundle.lists, 'products'):
                self.simulation_definitions.products = bundle.lists.products
                
        except Exception as e:
            # Fallback to defaults if bundle loading fails
            print(f"Warning: Failed to load simulation definitions from bundle: {e}")

    def _load_primary_mapping_from_bundle(self, bundle) -> None:
        """Load primary mapping from the bundle.
        
        Args:
            bundle: Phase1Bundle containing the primary mapping
        """
        try:
            # Load primary mapping from bundle
            if hasattr(bundle, 'primary_map') and hasattr(bundle.primary_map, 'long'):
                # Convert bundle primary mapping to UI state format using the long table
                self.primary_map.by_sector = {}
                
                # Group by sector and create entries
                for _, row in bundle.primary_map.long.iterrows():
                    sector = row['Sector']
                    product = row['Material']
                    start_year = row['StartYear']
                    
                    if sector not in self.primary_map.by_sector:
                        self.primary_map.by_sector[sector] = []
                    
                    entry = PrimaryMapEntry(product=product, start_year=start_year)
                    self.primary_map.by_sector[sector].append(entry)
                
                # Sort entries by product name for consistency
                for sector in self.primary_map.by_sector:
                    self.primary_map.by_sector[sector].sort(key=lambda x: x.product)
                        
        except Exception as e:
            # Fallback to empty mapping if bundle loading fails
            print(f"Warning: Failed to load primary mapping from bundle: {e}")

    def _initialize_client_revenue_state_from_bundle(self, bundle) -> None:
        """Initialize client revenue state with proper defaults after loading constants.
        
        This ensures that parameters not defined in the scenario get proper default values,
        including 0.0 for ramp_requirement_rate and steady_requirement_rate for inheritance.
        
        Args:
            bundle: Phase1Bundle containing the primary mapping
        """
        try:
            # Get sector-product combinations from primary mapping
            combinations = []
            for sector, entries in self.primary_map.by_sector.items():
                for entry in entries:
                    combination = f"{sector}_{entry.product}"
                    combinations.append(combination)
            
            if not combinations:
                return
            
            # Initialize market activation parameters
            if not self.client_revenue.market_activation_params:
                self.client_revenue.market_activation_params = {}
            
            for sp in combinations:
                if sp not in self.client_revenue.market_activation_params:
                    self.client_revenue.market_activation_params[sp] = {}
                
                # Set defaults only for parameters that aren't already set
                # Load defaults from bundle if available, otherwise use hardcoded fallbacks
                bundle_defaults = getattr(bundle, 'defaults', {})
                client_revenue_defaults = bundle_defaults.get('client_revenue', {})
                market_activation_defaults = client_revenue_defaults.get('market_activation', {})
                
                defaults = {
                    "ATAM": market_activation_defaults.get("ATAM", 50.0),
                    "anchor_start_year": market_activation_defaults.get("anchor_start_year", 2025.0),
                    "anchor_lead_generation_rate": market_activation_defaults.get("anchor_lead_generation_rate", 10.0),
                    "lead_to_pc_conversion_rate": market_activation_defaults.get("lead_to_pc_conversion_rate", 0.3),
                    "project_generation_rate": market_activation_defaults.get("project_generation_rate", 2.0),
                    "project_duration": market_activation_defaults.get("project_duration", 4.0),
                    "projects_to_client_conversion": market_activation_defaults.get("projects_to_client_conversion", 0.4),
                    "max_projects_per_pc": market_activation_defaults.get("max_projects_per_pc", 3.0),
                    "anchor_client_activation_delay": market_activation_defaults.get("anchor_client_activation_delay", 2.0)
                }
                
                for param, default_value in defaults.items():
                    if param not in self.client_revenue.market_activation_params[sp]:
                        self.client_revenue.market_activation_params[sp][param] = default_value
            
            # Initialize orders parameters
            if not self.client_revenue.orders_params:
                self.client_revenue.orders_params = {}
            
            for sp in combinations:
                if sp not in self.client_revenue.orders_params:
                    self.client_revenue.orders_params[sp] = {}
                
                # Set defaults only for parameters that aren't already set
                # Load defaults from bundle if available, otherwise use hardcoded fallbacks
                orders_defaults = client_revenue_defaults.get('orders', {})
                
                defaults = {
                    "initial_phase_duration": orders_defaults.get("initial_phase_duration", 2.0),
                    "initial_requirement_rate": orders_defaults.get("initial_requirement_rate", 100.0),
                    "initial_req_growth": orders_defaults.get("initial_req_growth", 0.2),
                    "ramp_phase_duration": orders_defaults.get("ramp_phase_duration", 3.0),
                    # Phase inheritance: ramp_requirement_rate defaults to 0 (inherit from initial phase end)
                    "ramp_requirement_rate": orders_defaults.get("ramp_requirement_rate", 0.0),
                    "ramp_req_growth": orders_defaults.get("ramp_req_growth", 0.15),
                    # Phase inheritance: steady_requirement_rate defaults to 0 (inherit from ramp phase end)
                    "steady_requirement_rate": orders_defaults.get("steady_requirement_rate", 0.0),
                    "steady_req_growth": orders_defaults.get("steady_req_growth", 0.1),
                    "requirement_to_order_lag": orders_defaults.get("requirement_to_order_lag", 1.0),
                    # NEW: Override parameters (default to 0 for inherited behavior)
                    "ramp_requirement_rate_override": orders_defaults.get("ramp_requirement_rate_override", 0.0),
                    "steady_requirement_rate_override": orders_defaults.get("steady_requirement_rate_override", 0.0),
                    # NEW: Requirement growth limit (percentage multiplier of initial rate)
                    "requirement_limit_multiplier": orders_defaults.get("requirement_limit_multiplier", 100.0)
                }
                
                for param, default_value in defaults.items():
                    if param not in self.client_revenue.orders_params[sp]:
                        self.client_revenue.orders_params[sp][param] = default_value
            
            # Initialize seeds parameters
            if not self.client_revenue.seeds_params:
                self.client_revenue.seeds_params = {}
            
            for sp in combinations:
                if sp not in self.client_revenue.seeds_params:
                    self.client_revenue.seeds_params[sp] = {}
                
                # Set defaults only for parameters that aren't already set
                # Load defaults from bundle if available, otherwise use hardcoded fallbacks
                seeds_defaults = client_revenue_defaults.get('seeds', {})
                
                defaults = {
                    "completed_projects_sm": seeds_defaults.get("completed_projects_sm", 0.0),
                    "active_anchor_clients_sm": seeds_defaults.get("active_anchor_clients_sm", 0.0),
                    "elapsed_quarters": seeds_defaults.get("elapsed_quarters", 0.0)
                }
                
                for param, default_value in defaults.items():
                    if param not in self.client_revenue.seeds_params[sp]:
                        self.client_revenue.seeds_params[sp][param] = default_value
                        
        except Exception as e:
            # Fallback if initialization fails
            print(f"Warning: Failed to initialize client revenue state from bundle: {e}")

    def _load_runspecs_defaults_from_bundle(self, bundle) -> None:
        """Load runspecs defaults from the bundle.
        
        Args:
            bundle: Phase1Bundle containing the defaults
        """
        try:
            bundle_defaults = getattr(bundle, 'defaults', {})
            runspecs_defaults = bundle_defaults.get('runspecs', {})
            
            if runspecs_defaults:
                # Only update if not already set from scenario
                if not hasattr(self.runspecs, '_loaded_from_scenario'):
                    self.runspecs.starttime = runspecs_defaults.get('starttime', self.runspecs.starttime)
                    self.runspecs.stoptime = runspecs_defaults.get('stoptime', self.runspecs.stoptime)
                    self.runspecs.dt = runspecs_defaults.get('dt', self.runspecs.dt)
                    self.runspecs.anchor_mode = runspecs_defaults.get('anchor_mode', self.runspecs.anchor_mode)
                
        except Exception as e:
            # Fallback if loading fails
            print(f"Warning: Failed to load runspecs defaults from bundle: {e}")

    # --- Snapshot helpers ---
    def snapshot_as_last_saved(self) -> None:
        """Record the current overrides as last-saved baseline for Reset buttons."""
        self.last_saved_constants = {k: float(v) for k, v in self.overrides.constants.items()}
        self.last_saved_points = {k: list(v) for k, v in self.overrides.points.items()}
        self.last_saved_seeds = {
            "active_anchor_clients": dict(self.seeds.active_anchor_clients),
            "elapsed_quarters": dict(self.seeds.elapsed_quarters),
            "direct_clients": dict(self.seeds.direct_clients),
            "active_anchor_clients_sm": {s: dict(m) for s, m in self.seeds.active_anchor_clients_sm.items()},
            "elapsed_quarters_sm": {s: dict(m) for s, m in self.seeds.elapsed_quarters_sm.items()},
            "completed_projects": dict(self.seeds.completed_projects),
            "completed_projects_sm": {s: dict(m) for s, m in self.seeds.completed_projects_sm.items()},
        }


__all__ = [
    "RunspecsState",
    "SimulationDefinitionsState",
    "ClientRevenueState", 
    "DirectMarketRevenueState",
    "LookupPointsState",
    "RunnerState",
    "LogsState",
    "ScenarioOverridesState",
    "PrimaryMapEntry",
    "PrimaryMapState",
    "SeedsState",
    "UIState",
]
