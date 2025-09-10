## Product Growth System – Codebase Index

This document provides a concise overview of the repository layout, the purpose of each directory/file, and how they work together. Use it as a quick reference when navigating the codebase.

### Top-level
- `simulate_growth.py`: Stepwise runner (Phase 7). Configures logging, loads Phase 1 inputs, loads and validates a single scenario (Phase 3), builds the SD model (Phase 4/6 + Phase 7 sector signals), and executes the stepwise SD+ABM loop (instantiate agents → act → aggregate → set gateways → advance using scheduler). **CRITICAL FIX**: Implements real-time KPI capture during the stepwise loop to prevent gateway corruption where post-run evaluation would use final-step gateway values across all time periods. Phase 9 adds scenario override echo to `logs/` and strict per-step validations (Agents_To_Create integer/non-negative, Fulfillment_Ratio bounds, revenue identity). Phase 11 adds `--preset` for selecting scenarios from `scenarios/`, validates scenario override keys against built model elements prior to application, and writes an additional suffixed CSV `Product_Growth_System_Complete_Results_<scenario>.csv` alongside the default file for easy comparisons. Phase 12 adds an optional `--visualize` flag to generate plots from the output CSV without touching SD/ABM logic. Phase 17.4 wires SM‑mode in the runner: uses per‑(sector, product) creation signals `Agents_To_Create_<s>_<p>`, instantiates `AnchorClientAgentSM` per pair (from `lists_sm`), aggregates requirements per (s,p), initializes `CPC_<s>_<p>`/`Cumulative_Agents_Created_<s>_<p>` when seeding, and captures per‑sector Anchor Leads by summing `Anchor_Lead_Generation_<s>_<p>` when sector‑level lead converters are absent.
  - Phase 17.6: Optional granular KPI rows (strictly opt-in). New flags `--kpi-sm-revenue-rows` and `--kpi-sm-client-rows` append per‑(sector, product) diagnostics to the CSV: `Revenue <sector> <product>` and `Anchor Clients <sector> <product>` respectively. Default CSV shape remains unchanged when flags are not used.
  - Phase 14: Supports scenario-based seeding via `seeds.active_anchor_clients` (optional `seeds.elapsed_quarters`) and `seeds.direct_clients` per product. Seeds are instantiated at t0: anchors as ACTIVE agents (in addition to SD outflow), direct clients by initializing `C_<product>`. Gating and monitoring reflect anchor seeds by setting `CPC_<sector>` and `Cumulative_Agents_Created_<sector>` stock initial values.
  - Phase 17.x: Completed-projects seeding for anchors. New keys `seeds.completed_projects` (sector-mode) and `seeds.completed_projects_sm` (SM-mode) let you pre-load a backlog of completed projects at t0. The runner converts backlog deterministically: `num_active = floor(completed / projects_to_client_conversion)` immediate ACTIVE anchors per sector/pair (respecting scenario overrides), with the remainder applied to a POTENTIAL agent's completed counter for near-term activation. SD stocks `CPC_*` and `Cumulative_Agents_Created_*` initial values are increased to reflect the additional ACTIVE anchors so ATAM gating and monitoring are consistent.
  - **SM Mode Fix**: Added `requirement_limit_multiplier` to the required parameters list for SM mode validation. This parameter was missing from the validation logic, causing simulations to crash when using `anchor_mode: "sm"` with incomplete parameter coverage.
  - NEW (Quarter semantics debugging): Emits optional DEBUG snapshots for early, midpoint, and last steps showing CPC vs ATAM per sector, CL vs TAM per product, and per-product `Potential_Clients`, `C`, and `Client_Creation` to verify per-quarter pacing.
  - Phase 15: Variable horizon. The runner and extractor emit one column per simulated step using labels derived from the time grid (`starttime`, `dt`, `num_steps`). Lead KPIs are reported per-step by scaling per-year SD converters by `dt`. Lookup tail policy is hold-last-value, with WARN logs when the grid is outside the defined points.
  - Phase 16: Anchor per-(sector, product) parameters. Scenarios and inputs can set per-(s,p) requirement phase parameters and lag. The model builds per-(s,p) constants with precedence (use per-(s,p) if provided else sector-level). Scenario overrides accept per-(s,p) constant names.
- `ui/`: Streamlit GUI rebuilt from scratch (Phase 1 scaffold completed).
  - `ui/app.py`: Minimal 9‑tab entrypoint wiring (Simulation Definitions, Simulation Specs, Primary Mapping, Seeds, Client Revenue, Direct Market Revenue, Lookup Points, Runner, Logs).
  - `ui/state.py`: Rich typed state retained for compatibility; simplification scheduled for later phases.
  - `ui/components/`: New base component and tab stubs (`*_tab.py`) replacing legacy editors.
  - `ui/services/`: New services replacing legacy ones: `scenario_service.py` (YAML I/O + validation), `validation_service.py` (light validators), `execution_service.py` (runner integration; hardened status; results discovery helpers; supports `--output-name`).
  - `ui/utils/`: Small helpers.
  - Phase 2 (UI behavior): Scenario saves now include a complete snapshot of `overrides.primary_map` reflecting the UI mapping for all sectors; in SM mode, `lists_sm` is auto-synchronized from the mapping on save to ensure the per‑(sector, product) universe matches the UI.
- `implementation_plan.md`: Executable plan for phased delivery (Phase 0 → Phase 11). **Phases 1-8 COMPLETED**: Complete 9-tab structure with all functionality implemented including table-based input, save protection, dynamic content management, scenario execution controls, and simulation monitoring.
- `technical_architecture.md`: System design and canonical naming/equations for SD+ABM integration; scenario schema and KPIs.
- `system logic.txt`: Plain-language system logic capturing business intent and discrete-conversion behavior.
- `requirements.txt`: Python dependencies (now pinned). Installed in `venv/` in development. BPTK_Py pinned to `2.1.1` to match the runner's API usage (`evaluate_equation`, `run_step`, `SimultaneousScheduler`).
- `Makefile`: Phase 12 packaging convenience. Targets: `venv`, `install`, `run_ui`, `run_baseline`, `test`, `lint`, `clean`.
- `Dockerfile.ui`: Optional container for the UI only. Mount `scenarios/`, `logs/`, and `output/` as volumes.
- `LICENSE`: Project license.
- `make_lint.py`: Helper to run lint/format tasks (optional tooling). **ENHANCED**: Now includes CSV extraction functionality via `--extract-csv` flag.
- `extract_csv_to_inputs.py`: **NEW** - Comprehensive CSV to inputs.json extraction script. Processes four CSV files (index.csv, anchor_client.csv, direct_clients.csv, points.csv) and transforms them into the proper inputs.json structure with proper parameter name mapping, default value handling, and validation.
- `index.md`: You are here. High-level map of the codebase.

### Directories
- `src/`: Python source code.
  - `io_paths.py`: Centralized absolute paths to `Inputs/`, `scenarios/`, `logs/`, and `output/`. Avoids hard-coded relative paths.
  - `utils_logging.py`: Logging configuration utility to write to console and `logs/run.log` with an optional debug flag.
  - `phase1_data.py`: Phase 1 JSON ingestion and validation.
    - Loads consolidated `inputs.json` from the project root (JSON-only; no CSV fallbacks). If a directory path is passed (e.g., `Path('Inputs')`), it resolves to `<dir>/inputs.json` if present, otherwise falls back to root `inputs.json`.
    - Parses into canonical DataFrames preserving legacy shapes: `AnchorParams.by_sector` (parameters × sectors), `OtherParams.by_product` (parameters × products), `ProductionTable.long` ([Year, Product, Capacity]), `PricingTable.long` ([Year, Product, Price]), and `PrimaryProductMap.long` ([Sector, Product, StartYear]).
    - Reconstructs `ListsData` as Market/Sector/Product combinations. Phase 3 enforces US-only scope: reconstructed lists must include `'US'`; error otherwise. A TODO remains for future EU/other market filtering.
    - Validation enhanced in Phase 3: strict `'lists'` presence in `inputs.json`, US-only check, start-year warnings (`StartYear <= 0`) in primary map, with existing checks for table coverage and monotonic years.
     - Exposes `Phase1Bundle` with lists, parameter tables, tables, and mappings. Phase 16: adds `anchor_sm` (long [Sector, Product, Param, Value]) and `lists_sm` (explicit or derived SP universe) with validations that (s,p) references exist. Phase 17.1: tracks `lists_sm_explicit` to enforce that SM-mode uses an explicit SP universe.
- `naming.py`: Phase 2 canonical naming utilities.
  - `create_element_name` normalizes base/sector/product into BPTK-compatible names with collision safety.
  - Helper functions generate canonical names for SD elements and scenario override constants/lookups. Phase 17.2 adds helpers for SM-mode per-(s,p) creation signals (`Anchor_Lead_Generation_<s>_<p>`, `CPC_<s>_<p>`, `New_PC_Flow_<s>_<p>`, `Agent_Creation_Accumulator_<s>_<p>`, `Agent_Creation_Inflow_<s>_<p>`, `Agent_Creation_Outflow_<s>_<p>`, `Agents_To_Create_<s>_<p>`, `Cumulative_Agents_Created_<s>_<p>`).
- `scenario_loader.py`: Phase 3 scenario loader and strict validation.
  - Loads YAML/JSON scenario, applies default runspecs, derives permissible override keys from `Phase1Bundle`, validates constants and lookup points, and returns a normalized `Scenario` dataclass.
  - Public helper APIs for the UI: `list_permissible_override_keys`, `validate_scenario_dict`, and `summarize_lists` (non‑breaking; surface existing logic for UI consumption).
  - Phase 11: provides `validate_overrides_against_model(model, scenario)` to assert that every override constant and lookup maps to a constructed model element, preventing partial application or name drift.
  - Phase 14: validates optional `seeds` block (scenario-specific): `active_anchor_clients` and optional `elapsed_quarters` per sector (non-negative integers, sectors must exist). Exposes normalized maps on the `Scenario` object.
  - Phase 16: expands permissible constants to include per-(s,p) names across the SP universe (from `lists_sm` or `primary_map`) for targeted params.
  - Phase 17.1: adds global mode switch `runspecs.anchor_mode: "sector" | "sm"` (default `"sector"`). In SM-mode, sector-level anchor constant overrides are disallowed; only per-(sector, product) targeted constants are accepted. Requires explicit `lists_sm` in `inputs.json` and complete `anchor_params_sm` coverage for all targeted parameters and pairs; also adds `seeds.active_anchor_clients_sm` and prohibits sector-level seeding in SM-mode.
  - Phase 17.2: in SM-mode, permissible override surface expands to the full per-(s,p) anchor set listed in the implementation plan (including timing, lifecycle, phase durations/rates/growths, ATAM, and requirement-to-order lag).
- `growth_model.py`: Phase 4/6 SD model with Phase 7 prerequisites. Phase 4: direct clients with **NEW cohort-based order system**, capacity and price lookups, fulfillment ratio, client delivery flows, and client revenue (JSON-first ingestion; price/capacity lookups are built from `inputs.json`). **NEW: Direct client cohort aging chain**: Clients are organized into cohorts by creation quarter, with each cohort starting at base order quantity and growing linearly over time with per-client order limits. Phase 6: ABM→SD gateways per sector–product, aggregated agent demand into `Total_Demand_<p>`, delayed sector–product anchor deliveries with sector or per-(s,p) lags, and product-level anchor delivery aggregation. Phase 7 prereqs: anchor constants for all sectors and sector-level agent-creation signals (`Agents_To_Create_<sector>`). Phase 16: creates per-(s,p) constants for `requirement_to_order_lag` and phase parameters with precedence (use per-(s,p) if provided else sector-level), and uses `requirement_to_order_lag_<s>_<p>` in anchor deliveries. Phase 17.2: when `runspecs.anchor_mode == "sm"`, builds a per-(s,p) creation pipeline for every pair in `lists_sm` and does not create any sector-level creation signals; otherwise builds the legacy sector-level creation. Phase 17.5: in SM‑mode, all per‑(s,p) anchor parameters (phase rates/growths and lags) are required with no sector fallbacks; sector-mode retains legacy precedence. Provides `apply_scenario_overrides` for constants and lookup points. **Delay Fix**: Implements `_apply_delay_with_offset()` helper function to correct BPTK_Py's delay timing behavior, ensuring intuitive delay behavior where 1-quarter delay parameters produce exactly 1-quarter delays.
  - NEW (Quarter correctness): Per-quarter inputs are converted to per-year at the source so that with `dt=0.25` the integrated increment per step equals the intended per-quarter amount:
    - `Anchor_Lead_Generation_<sector>` is multiplied by 4; `CPC_<sector>` integrates this directly.
    - `Inbound_Leads_<product>` and `Outbound_Leads_<product>` are multiplied by 4; `CL_<product>` integrates total new leads accordingly.
    - Average order quantity compounding uses elapsed quarters: `(Time - lead_start_year) / 0.25`.
  - Note: Accumulate-and-fire integer drains remain unscaled in stock derivatives; we validate discrete creation pacing via DEBUG snapshots and may introduce a dedicated "drain" converter in a future step if needed.
  - `__init__.py`: Marks `src` as a package and re-exports key APIs (naming, ABM agents).
- `abm_anchor.py`: Phase 5 Anchor Client ABM implementation. Provides `AnchorClientAgent` with deterministic lifecycle (projects → activation → multi-phase requirements), and factories (`build_anchor_agent_factory_for_sector`, `build_all_anchor_agent_factories`) driven by Phase 1 inputs. **TIMING FIX**: Project completion logic reordered to ensure proper in-progress duration for Active Projects KPI. Phase 16: agents accept optional per-(s,p) requirement phase overrides (initial/ramp/steady rate/growth) provided by the factory from `anchor_params_sm`. Phase 17.3: introduces `AnchorClientAgentSM` (self-contained per-(sector, product) lifecycle) and `build_sm_anchor_agent_factory(sector, product)` with strict per-(s,p) parameter sourcing (no sector fallbacks) and deterministic phase requirements gated by `anchor_start_year_<s>_<p>`. **NEW**: Added `requirement_limit_multiplier` parameter to prevent unlimited requirement growth with hard stop behavior.
- `kpi_extractor.py`: Phase 8 KPI extraction and CSV writer. Evaluates canonical SD element names per step and uses runner-managed agent state to compute KPIs, then writes `output/Product_Growth_System_Complete_Results.csv`. **GATEWAY FIX**: Accepts `kpi_values_by_step` captured during the run to avoid post-run corruption. The public API `extract_and_write_kpis` requires a per-step ABM metrics list. 
    - Phase 15: Variable horizon supported. Emits exactly `num_steps` columns with labels derived from the time grid. Lead KPIs are expected to be passed from the runner's real-time capture where per-year signals are scaled by `dt` to per-step units.
  - `validation.py`: Phase 9 validation and echo utilities (scenario override echo, gateway sampling, and per-step validations for Agents_To_Create, Fulfillment_Ratio bounds, and revenue identity).
  - `validation.py`: Phase 9 validation and echo utilities (scenario override echo, gateway sampling, and per-step validations for Agents_To_Create, Fulfillment_Ratio bounds, and revenue identity). Phase 17.7: scenario echo now also records `runspecs.anchor_mode` and all `seeds.*` blocks (including `active_anchor_clients_sm`) for traceability.

- `tests/`: Unit tests.
  - `test_naming.py`: Tests for Phase 2 naming utilities (normalization, truncation stability, registry collision detection, helper alignment).
  - `test_scenario_loader.py`: Tests for Phase 3 scenario validation (runspec defaults, unknown keys, points sorting, monotonicity checks).
  - `test_phase4_model.py`: Tests for Phase 4 model build and scenario override application.
  - `test_phase5_agents.py`: Tests for Phase 5 AnchorClientAgent factories, lifecycle transitions to ACTIVE, per-product requirement generation, and determinism.
  - `test_phase7_runner.py`: Tests for Phase 7 scaffolding (gateway updates and stepwise evaluation without a scheduler).
  - `test_phase6_gateways.py`: Tests for Phase 6 gateways and anchor deliveries presence and updateability.
  - `test_phase7_scheduler_integration.py`: Scheduler integration test; two-step run with gateway updates and bounds checks (aggregated demand, fulfillment ratio, anchor deliveries).
  - `test_runner_smoke_e2e.py`: End-to-end runner smoke test over a short horizon (no outputs written) ensuring the loop completes without errors.
  - `test_delay_behavior.py`: Basic delay-behavior checks for anchor/client flows under the scheduler.
  - `test_price_sensitivity.py`: Price override sensitivity sanity (lookup override reflected in converter evaluation).
  - `test_phase10_regression.py`: Phase 10 baseline regression. Runs the stepwise runner with `scenarios/baseline.yaml`, compares the generated KPI CSV structure and, where provided, numeric values to `Inputs/Expected Output.csv`. Placeholder rows with `{Sector}`/`{Product}` are expanded from `Inputs/Lists.csv`.
  - `test_phase7_8_components.py`: **NEW** - Tests for Phase 7-8 UI components (lookup points, runner, and logs tabs) validating functionality, state management, and integration.
  - `conftest.py`: Ensures repo root is on `sys.path` so tests can import from `src` without extra environment setup.

- `Inputs/`: Legacy CSVs previously used for ingestion. Retained for historical reference and Phase 10 regression inputs but not used by Phase 1 ingestion anymore.
  - `Lists.csv`, `Anchor Client Parameters.csv`, `Other Client Parameters.csv`, `Production Table.csv`, `Pricing Table.csv`, `Primary Product.csv`.
  - `Expected Output.csv`, `Product_Growth_System_Complete_Results.csv`: Baseline outputs for validation/regression.

- `scenarios/`:
  - `baseline.yaml`: Minimal scenario with `runspecs` and empty `overrides` block. Use this as a template.
  - `price_shock.yaml`: Example preset with higher prices for selected products.
  - `high_capacity.yaml`: Example preset with higher capacity for a product. Points are yearly; model scales to per-quarter internally.
  - `price_shock.yaml`: Example Phase 11 preset increasing product prices (points under `price_<product>`).
  - `high_capacity.yaml`: Example Phase 11 preset boosting capacity for a product (points under `max_capacity_<product>`). Points are yearly; the model converts capacity to per-quarter internally.
  - `multi_product_defense_aviation.yaml`: Phase 13 scenario using multi-product sector mapping from `inputs.json` (Defense includes Silicon Nitride Fiber; Aviation includes Boron_fiber starting 2026). No overrides; demonstrates multi-product anchors.
  - `pm_override_example.yaml`: Phase 13 scenario demonstrating `overrides.primary_map` to replace sector→products mapping directly from a scenario.
  - `sm_minimal.yaml`: Phase 17.7 minimal SM-mode scenario (`anchor_mode: sm`) relying on `inputs.json` `lists_sm`/`anchor_params_sm`, with a single SP seed.
  - `sm_full_demo.yaml`: Phase 17.7 SM-mode demo with per-(s,p) constant overrides and multiple SP seeds.
  - `cohort_test.yaml`: **NEW** - Simple cohort system test scenario with controlled parameters for `Silicon_Carbide_Fiber` to demonstrate cohort aging and per-client caps.
  - `direct_only_cohort.yaml`: **NEW** - Direct client cohort test scenario isolating direct client behavior with neutralized anchor leads.

- `logs/`:
  - `run.log`: Latest run logs when using the runner.
  - `scenario_overrides_echo.json`/`.yaml`: Echo of applied scenario overrides (Phase 9). Includes `anchor_mode` and `seeds` blocks (Phase 17.7).

- `output/`:
  - Generated CSV outputs. Phase 8 writes `Product_Growth_System_Complete_Results.csv`.
  - `plots/`: Phase 12 image outputs when `--visualize` is used.

### **CSV Data Integration (NEW)**

The system now supports extracting data from CSV files and integrating them into the `inputs.json` structure:

**CSV Files Processed:**
- `Inputs/index.csv`: Market, sector, and material lists
- `Inputs/anchor_client.csv`: Per-(sector, material) anchor client parameters (21 parameters across 9 combinations)
- `Inputs/direct_clients.csv`: Material-specific direct client parameters (9 parameters)
- `Inputs/points.csv`: Production capacity and pricing time series data (2025-2031)

**Extraction Process:**
1. **Parameter Name Mapping**: Converts CSV parameter names (with descriptive text) to canonical system names
2. **Sector-Material Parsing**: Properly separates sector and material names from combined column headers
3. **Default Value Handling**: Adds sensible defaults for missing materials/parameters
4. **Data Validation**: Ensures complete coverage and proper data types
5. **Structure Generation**: Creates proper `inputs.json` with lists, parameters, production/pricing data, and primary mapping

**Usage:**
```bash
# Extract CSV data and create inputs.json
python make_lint.py --extract-csv

# Or run directly
python extract_csv_to_inputs.py
```

**Real Data Integration:**
- **Markets**: US, EU
- **Sectors**: Defense, Nuclear, Semiconductors, Aviation
- **Materials**: Silicon_Carbide_Fiber, Silicon_Carbide_Powder, Silicon_Nitride_Fiber, UHT, Boron_fiber, B4C_Fiber, WC_Fiber, AUF
- **Sector-Material Combinations**: 9 real combinations (e.g., Defense + Silicon_Carbide_Fiber, Nuclear + AUF)
- **Production Data**: Real capacity projections 2025-2031
- **Pricing Data**: Real price projections 2025-2031

### **NEW UI STRUCTURE (Phases 1-3 Completed)**

The UI has been restructured to use a new 9-tab system as specified in the implementation plan:

**Tab 1: Simulation Definitions** ✅ **COMPLETED**
- Market, sector, and product list management
- Table-based input with add/edit/delete functionality
- Save button protection to prevent accidental changes
- Dynamic content management

**Tab 2: Simulation Specs** ✅ **COMPLETED (Phase 3)**
- Runtime controls (start time, stop time, dt)
- Anchor mode selection (Sector vs Sector+Product mode)
- Enhanced with save protection and change tracking
- Scenario management (load, reset to baseline)
- Comprehensive validation and state management

**Tab 3: Primary Mapping** ✅ **COMPLETED (Phase 4)**
- Sector-wise product selection
- Mapping insights and summary
- Dynamic table generation
- Save protection and change tracking
- Enhanced visual organization and feedback

**Tab 4: Seeds** ✅ **COMPLETED (Phase 4 - Enhanced)**
- **NEW**: Dedicated seeds configuration tab
- SM-mode and sector-mode seeding support
- Primary Mapping integration (only shows relevant combinations)
- Case-insensitive lookup for robust handling
- Active anchor clients, elapsed quarters, and completed projects
- Direct client configuration per product

**Tab 5: Client Revenue** ✅ **COMPLETED (Phase 5 - Updated)**
- Comprehensive parameter tables (19 parameters)
- Market Activation and Orders groups
- **UPDATED**: Removed seeds parameters (now handled by dedicated Seeds tab)
- Dynamic content based on primary mapping
- Table-based input with save button protection
- Organized in two logical groups with descriptions
- **NEW**: Added `requirement_limit_multiplier` parameter for per-client order caps in cohort system

**Tab 6: Direct Market Revenue** ✅ **COMPLETED (Phase 6)**
- Product-specific parameters (9 parameters)
- Dynamic content based on primary mapping
- Table-based input with save button protection
- Comprehensive parameter coverage for direct market revenue

**Tab 7: Lookup Points** ✅ **COMPLETED (Phase 3)**
- Time-series production capacity and pricing (tables; Enter-to-commit)
- Year-based structure with products as columns

**Tab 8: Runner** ✅ **Controls Only**
- Scenario validation and execution controls wired to backend runner
- Status display (PID, scenario, start time) and manual refresh
- Runs `simulate_growth.py` with flags (debug, plots, optional SM KPI rows)

**Tab 9: Logs** ✅ **COMPLETED**
**Tab 10: Results** ✅ **COMPLETED**
- Latest CSV preview from `output/`
- Recent plots from `output/plots/`
- Clear empty state when no results exist
- Real engine logs from `logs/run.log`
- Level filter, substring filter, adjustable tail size
- File statistics, file path/size when present, and "Download visible tail" export
- Clear guidance when the log file does not yet exist
- Optional auto-refresh via `streamlit-autorefresh` (manual refresh otherwise)

Reset behavior: Parameter tables (Client Revenue, Direct Market Revenue) and Lookup Points now support deterministic per‑subtab Reset that rebuilds from last‑saved YAML and rotates editor keys to force a clean redraw. Seeds tab also supports Reset to last‑saved values.


