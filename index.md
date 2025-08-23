## Product Growth System – Codebase Index

This document provides a concise overview of the repository layout, the purpose of each directory/file, and how they work together. Use it as a quick reference when navigating the codebase.

### Top-level
- `simulate_growth.py`: Stepwise runner (Phase 7). Configures logging, loads Phase 1 inputs, loads and validates a single scenario (Phase 3), builds the SD model (Phase 4/6 + Phase 7 sector signals), and executes the stepwise SD+ABM loop (instantiate agents → act → aggregate → set gateways → advance using scheduler). **CRITICAL FIX**: Implements real-time KPI capture during the stepwise loop to prevent gateway corruption where post-run evaluation would use final-step gateway values across all time periods. Phase 9 adds scenario override echo to `logs/` and strict per-step validations (Agents_To_Create integer/non-negative, Fulfillment_Ratio bounds, revenue identity). Phase 11 adds `--preset` for selecting scenarios from `scenarios/`, validates scenario override keys against built model elements prior to application, and writes an additional suffixed CSV `Product_Growth_System_Complete_Results_<scenario>.csv` alongside the default file for easy comparisons. Phase 12 adds an optional `--visualize` flag to generate plots from the output CSV without touching SD/ABM logic. Phase 17.4 wires SM‑mode in the runner: uses per‑(sector, product) creation signals `Agents_To_Create_<s>_<p>`, instantiates `AnchorClientAgentSM` per pair (from `lists_sm`), aggregates requirements per (s,p), initializes `CPC_<s>_<p>`/`Cumulative_Agents_Created_<s>_<p>` when seeding, and captures per‑sector Anchor Leads by summing `Anchor_Lead_Generation_<s>_<p>` when sector‑level lead converters are absent.
  - Phase 17.6: Optional granular KPI rows (strictly opt-in). New flags `--kpi-sm-revenue-rows` and `--kpi-sm-client-rows` append per‑(sector, product) diagnostics to the CSV: `Revenue <sector> <product>` and `Anchor Clients <sector> <product>` respectively. Default CSV shape remains unchanged when flags are not used.
  - Phase 14: Supports scenario-based seeding via `seeds.active_anchor_clients` (optional `seeds.elapsed_quarters`) and `seeds.direct_clients` per product. Seeds are instantiated at t0: anchors as ACTIVE agents (in addition to SD outflow), direct clients by initializing `C_<product>`. Gating and monitoring reflect anchor seeds by setting `CPC_<sector>` and `Cumulative_Agents_Created_<sector>` stock initial values.
  - Phase 17.x: Completed-projects seeding for anchors. New keys `seeds.completed_projects` (sector-mode) and `seeds.completed_projects_sm` (SM-mode) let you pre-load a backlog of completed projects at t0. The runner converts backlog deterministically: `num_active = floor(completed / projects_to_client_conversion)` immediate ACTIVE anchors per sector/pair (respecting scenario overrides), with the remainder applied to a POTENTIAL agent's completed counter for near-term activation. SD stocks `CPC_*` and `Cumulative_Agents_Created_*` initial values are increased to reflect the additional ACTIVE anchors so ATAM gating and monitoring are consistent.
  - NEW (Quarter semantics debugging): Emits optional DEBUG snapshots for early, midpoint, and last steps showing CPC vs ATAM per sector, CL vs TAM per product, and per-product `Potential_Clients`, `C`, and `Client_Creation` to verify per-quarter pacing.
  - Phase 15: Variable horizon. The runner and extractor emit one column per simulated step using labels derived from the time grid (`starttime`, `dt`, `num_steps`). Lead KPIs are reported per-step by scaling per-year SD converters by `dt`. Lookup tail policy is hold-last-value, with WARN logs when the grid is outside the defined points.
  - Phase 16: Anchor per-(sector, product) parameters. Scenarios and inputs can set per-(s,p) requirement phase parameters and lag. The model builds per-(s,p) constants with precedence (use per-(s,p) if provided else sector-level). Scenario overrides accept per-(s,p) constant names.
- `ui/`: Streamlit GUI scaffolding and services.
  - `ui/app.py`: Scenario Editor & Runner. Tabs for Runspecs, Constants, Points, Primary Map, Seeds, Validate & Save, and Run (Phases 3–9). In‑memory validation against backend helpers, YAML writer, preset manager (load/duplicate), run‑current functionality, log rendering during runs, and CSV preview.
  - `ui/state.py`: Typed UI state (`UIState`, `RunspecsState`, `ScenarioOverridesState`, `PrimaryMapState`, `SeedsState`) with helpers to assemble a scenario dict including `overrides.primary_map` and `seeds`, and `load_from_scenario_dict` to populate the editor from existing scenarios.
  - `ui/services/builder.py`: Runner integration helpers (build command, run, start/terminate process, file‑tail, find latest results, optional plot generation), scenario file utilities (`write_scenario_yaml`, `read_scenario_yaml`, `list_available_scenarios`).
  - `ui/services/validation_client.py`: Thin client to list permissible override keys and validate in‑memory scenarios.
  - `ui/components/`: UI widgets (`runspecs_form.py`, `constants_editor.py`, `points_editor.py`, `primary_map_editor.py`, `seeds_editor.py`).
- `implementation_plan.md`: Executable plan for phased delivery (Phase 0 → Phase 11). Follow this for scope, success criteria, tests, and acceptance.
- `technical_architecture.md`: System design and canonical naming/equations for SD+ABM integration; scenario schema and KPIs.
- `system logic.txt`: Plain-language system logic capturing business intent and discrete-conversion behavior.
- `requirements.txt`: Python dependencies (now pinned). Installed in `venv/` in development. BPTK_Py pinned to `2.1.1` to match the runner's API usage (`evaluate_equation`, `run_step`, `SimultaneousScheduler`).
- `Makefile`: Phase 12 packaging convenience. Targets: `venv`, `install`, `run_ui`, `run_baseline`, `test`, `lint`, `clean`.
- `Dockerfile.ui`: Optional container for the UI only. Mount `scenarios/`, `logs/`, and `output/` as volumes.
- `LICENSE`: Project license.
- `make_lint.py`: Helper to run lint/format tasks (optional tooling).
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
- `growth_model.py`: Phase 4/6 SD model with Phase 7 prerequisites. Phase 4: direct clients, capacity and price lookups, fulfillment ratio, client delivery flows, and client revenue (JSON-first ingestion; price/capacity lookups are built from `inputs.json`). Phase 6: ABM→SD gateways per sector–product, aggregated agent demand into `Total_Demand_<p>`, delayed sector–product anchor deliveries with sector or per-(s,p) lags, and product-level anchor delivery aggregation. Phase 7 prereqs: anchor constants for all sectors and sector-level agent-creation signals (`Agents_To_Create_<sector>`). Phase 16: creates per-(s,p) constants for `requirement_to_order_lag` and phase parameters with precedence (use per-(s,p) if provided else sector-level), and uses `requirement_to_order_lag_<s>_<p>` in anchor deliveries. Phase 17.2: when `runspecs.anchor_mode == "sm"`, builds a per-(s,p) creation pipeline for every pair in `lists_sm` and does not create any sector-level creation signals; otherwise builds the legacy sector-level creation. Phase 17.5: in SM‑mode, all per‑(s,p) anchor parameters (phase rates/growths and lags) are required with no sector fallbacks; sector-mode retains legacy precedence. Provides `apply_scenario_overrides` for constants and lookup points.
  - NEW (Quarter correctness): Per-quarter inputs are converted to per-year at the source so that with `dt=0.25` the integrated increment per step equals the intended per-quarter amount:
    - `Anchor_Lead_Generation_<sector>` is multiplied by 4; `CPC_<sector>` integrates this directly.
    - `Inbound_Leads_<product>` and `Outbound_Leads_<product>` are multiplied by 4; `CL_<product>` integrates total new leads accordingly.
    - Average order quantity compounding uses elapsed quarters: `(Time - lead_start_year) / 0.25`.
  - Note: Accumulate-and-fire integer drains remain unscaled in stock derivatives; we validate discrete creation pacing via DEBUG snapshots and may introduce a dedicated "drain" converter in a future step if needed.
  - `__init__.py`: Marks `src` as a package and re-exports key APIs (naming, ABM agents).
- `abm_anchor.py`: Phase 5 Anchor Client ABM implementation. Provides `AnchorClientAgent` with deterministic lifecycle (projects → activation → multi-phase requirements), and factories (`build_anchor_agent_factory_for_sector`, `build_all_anchor_agent_factories`) driven by Phase 1 inputs. **TIMING FIX**: Project completion logic reordered to ensure proper in-progress duration for Active Projects KPI. Phase 16: agents accept optional per-(s,p) requirement phase overrides (initial/ramp/steady rate/growth) provided by the factory from `anchor_params_sm`. Phase 17.3: introduces `AnchorClientAgentSM` (self-contained per-(sector, product) lifecycle) and `build_sm_anchor_agent_factory(sector, product)` with strict per-(s,p) parameter sourcing (no sector fallbacks) and deterministic phase requirements gated by `anchor_start_year_<s>_<p>`.
- `kpi_extractor.py`: Phase 8 KPI extraction and CSV writer. Evaluates canonical SD element names per step and uses runner-managed agent state to compute KPIs, then writes `output/Product_Growth_System_Complete_Results.csv`. **GATEWAY FIX**: Accepts `kpi_values_by_step` captured during the run to avoid post-run corruption. The public API `extract_and_write_kpis` requires a per-step ABM metrics list. 
    - Phase 15: Variable horizon supported. Emits exactly `num_steps` columns with labels derived from the time grid. Lead KPIs are expected to be passed from the runner's real-time capture where per-year signals are scaled by `dt` to per-step units.
  - `validation.py`: Phase 9 validation and echo utilities (scenario override echo, gateway sampling, and per-step validations for Agents_To_Create, Fulfillment_Ratio bounds, and revenue identity).
  - `validation.py`: Phase 9 validation and echo utilities (scenario override echo, gateway sampling, and per-step validations for Agents_To_Create, Fulfillment_Ratio bounds, and revenue identity). Phase 17.7: scenario echo now also records `runspecs.anchor_mode` and all `seeds.*` blocks (including `active_anchor_clients_sm`) for traceability.

- `tests/`: Unit tests.
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

- `logs/`:
  - `run.log`: Latest run logs when using the runner.
  - `scenario_overrides_echo.json`/`.yaml`: Echo of applied scenario overrides (Phase 9). Includes `anchor_mode` and `seeds` blocks (Phase 17.7).

- `output/`:
  - Generated CSV outputs. Phase 8 writes `Product_Growth_System_Complete_Results.csv`.
  - `plots/`: Phase 12 image outputs when `--visualize` is used.


