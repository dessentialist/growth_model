## FFF Growth System – Implementation Plan (BPTK_Py SD + ABM, Stepwise Runner)

### Purpose
- Build a deterministic, hybrid System Dynamics (SD) + Agent-Based (ABM) model using BPTK_Py’s simple Python SD-DSL with a stepwise runner that updates ABM→SD gateway converters each simulation step.
- Strictly externalize all parameter values; do not hardcode defaults or use fallbacks. Every constant/lookup must originate from user-provided inputs (CSVs and/or scenario overrides).

### Non-Negotiables
- No fallback mechanisms, approximations, or simplifications beyond what is explicitly defined in the technical architecture.
- No hardcoded default parameter values in code. If an input is missing, the run must fail fast with a clear validation error; it must not silently substitute defaults.
- Deterministic execution order each step: instantiate agents → agent actions → aggregate material demand → set gateway values → advance SD → capture outputs.

### Key Characteristics, Behaviors, and Patterns (from technical architecture and system logic)
- Hybrid modeling pattern: SD for time-continuous dynamics; ABM for Anchor Client lifecycle and requirement phases.
- Discrete conversion (“accumulate-and-fire”) for direct clients to ensure integer client creation and realistic dynamics.
- Capacity sharing: a single time-varying capacity per material constrains both anchor and direct client deliveries via a fulfillment ratio.
- Multi-phase, per-agent requirement generation: initial → ramp → steady, with per-sector growth rates and activation delays.
- Time-varying lookups: price and capacity are defined as lookup tables by material and read at the current simulation time.
- Sector–material attribution: anchor demand and deliveries must retain sector attribution for revenue by sector.
- Scenario overrides are applied by exact element names to constants and lookups before simulation start; unknown override keys are validation errors (no substitutions).
- Outputs are quarterly series (dt = 0.25), 28 quarters, with strict KPI mapping.

---

## Phase 0 — Project Setup & Tooling
- Tasks
  - Create directories: `scenarios/`, `logs/`, `output/`.
  - Pin dependencies in `requirements.txt` to include `BPTK_Py==2.1.1` and `pandas`, and add `pyyaml` for YAML scenarios.
  - Add `make_lint.py` or a simple lint task and a formatter configuration (black/ruff if allowed) without reformatting unrelated code.
  - Establish a consistent time base: years for time axis; quarters used in delays/durations with dt = 0.25.
- Success Criteria
  - Repo structure matches guidance in the technical architecture; clean install works on a new machine.
  - A placeholder scenario file loads and validates (name + runspecs only).
- Testing
  - Smoke test: import of libraries succeeds; empty runner prints a banner and exits.
- Debugging
  - If environment import fails, print actionable hints (python version, pip list).

## Phase 1 — Data Ingestion & Validation (CSVs)
- Inputs
  - `Inputs/Lists.csv` (markets, sectors, materials)
  - `Inputs/Anchor Client Parameters.csv` (per sector)
  - `Inputs/Other Client Parameters.csv` (per material)
  - `Inputs/Production Table.csv` (capacity by material over time)
  - `Inputs/Pricing Table.csv` (price by material over time)
- Tasks
  - Implement robust CSV loader with cleaning rules: strip currency/percent, force numeric, guard NaNs, and sort time-series.
  - Build canonical mappings: sectors → primary materials, materials → sectors (as needed), and master lists.
  - Validate coverage: every sector and material referenced anywhere must have all required parameters present.
  - Enforce strictness: missing values ⇒ validation error; do not inject defaults.
- Success Criteria
  - DataFrames/dicts contain only numeric parameter values with complete coverage.
  - Time series (capacity, price) strictly increasing on time dimension, numeric, non-empty.
- Testing
  - Unit tests for cleaner functions (percent/currency parsing, sorting, numeric casting).
  - Unit tests for schema completeness (all required columns exist; no NaNs).
- Debugging
  - On failure, print which file, which row, which field is invalid, with the offending value and a remediation hint.

## Phase 2 — Element Naming Utilities
- Tasks
  - Implement `create_element_name(base[, sector][, material])` that:
    - Normalizes whitespace/punctuation to underscores.
    - Preserves readability; apply truncation only if necessary (hash-based suffix) to avoid collisions.
    - Guarantees stability across runs for the same inputs.
  - Provide helpers for canonical element names described in the architecture (e.g., `Anchor_Lead_Generation_<sector>`, `Price_<material>`).
- Success Criteria
  - All generated names exactly match those enumerated in the technical architecture sections.
  - Collision tests pass (distinct inputs yield distinct names, stable across runs).
- Testing
  - Unit tests for a representative set of sectors/materials with spaces and special characters.
- Debugging
  - On collision, raise with both colliding inputs and the computed names.

## Phase 3 — Scenario Loader (YAML/JSON) & Strict Overrides
- Tasks
  - Implement loader for a single scenario per run with `runspecs` and `overrides` blocks.
  - Validate `runspecs` (starttime, stoptime, dt) and ensure dt = 0.25 unless scenario explicitly overrides it.
  - Validate `overrides.constants` and `overrides.points` keys against the final model element names. Unknown keys ⇒ error.
  - Sort and validate lookup points (strictly numeric; ascending time).
- Success Criteria
  - Scenario is parsed; overrides stored in structures ready to apply to model elements by exact name.
  - Public UI helper APIs available: `list_permissible_override_keys`, `validate_scenario_dict`, `summarize_lists` (no behavior change; expose existing logic).
- Testing
  - Unit tests: good scenario, unknown constant key, malformed points, unsorted points (auto-sorted), non-numeric values.
- Debugging
  - Print nearest-name suggestions but still fail on mismatches; do not apply partial overrides.

## Phase 4 — SD Model: Direct Clients, Capacity, Lookups, Revenue (BPTK_Py SD-DSL)
- Tasks
  - Build a `Model` with elements per material m:
    - Constants/converters for: `lead_start_year_<m>`, `inbound_lead_generation_rate_<m>`, `outbound_lead_generation_rate_<m>`, `lead_to_c_conversion_rate_<m>`, `lead_to_requirement_delay_<m>`, `requirement_to_fulfilment_delay_<m>`, `avg_order_quantity_initial_<m>`, `client_requirement_growth_<m>`, `TAM_material_<m>`.
    - Stocks/flows for leads and clients with accumulate-and-fire discrete client creation:
      - `Inbound_Leads_<m>`, `Outbound_Leads_<m>`, `Total_New_Leads_<m>`
      - `Potential_Clients_<m>` (accumulates fractional conversions)
      - `Client_Creation_<m>` (integer fire) and `C_<m>` (cumulative clients)
    - Requirement and delay:
      - `avg_order_quantity_<m> = avg_order_quantity_initial_<m> * (1 + client_requirement_growth_<m>)^(max(0, time - lead_start_year_<m>))`
      - `Client_Requirement_<m> = delay(model, C_<m> * avg_order_quantity_<m>, lead_to_requirement_delay_<m>)`
    - Capacity and price lookups:
      - `max_capacity_lookup_<m> = lookup(time, max_capacity_<m>)`
      - `Price_<m> = lookup(time, price_<m>)`
    - Total demand and fulfillment ratio:
      - `Agent_Demand_Sector_Input_<s>_<m>` (converter per sector–material; numeric; set each step by runner)
      - `Agent_Aggregated_Demand_<m> = sum_s Agent_Demand_Sector_Input_<s>_<m>`
      - `Total_Demand_<m> = Agent_Aggregated_Demand_<m> + Client_Requirement_<m>`
      - `Fulfillment_Ratio_<m> = min(1, if Total_Demand_<m> > 0 then max_capacity_lookup_<m> / Total_Demand_<m> else 1)`
    - Deliveries & revenue:
      - `Delayed_Client_Demand_<m> = Client_Requirement_<m> * Fulfillment_Ratio_<m>`
      - `Client_Delivery_Flow_<m> = delay(model, Delayed_Client_Demand_<m>, requirement_to_fulfilment_delay_<m>)`
      - `Client_Revenue_<m> = Client_Delivery_Flow_<m> * Price_<m>`
  - Ensure equations use quarters directly; no dt scaling inside delays/durations.
- Success Criteria
  - Model compiles; all required per-material elements exist with exact names; no missing parameter references.
  - With zero agents and valid direct-client inputs, the model runs and produces non-negative flows and revenues.
- Testing
  - Unit tests for lookup creation and `delay` usage (single-material micro scenario).
  - Golden integration test with 1 material and handcrafted small dataset; compare against hand calculations.
- Debugging
  - If the scheduler raises dependency errors, print the element names involved and the offending equations.

## Phase 5 — ABM: AnchorClientAgent & Sector Factories
### UX Phases 3–5 — Streamlit Editor
- Scope
  - Add `ui/` Streamlit app with tabs: Runspecs, Constants, Points. Keep UI isolated from model.
- Tasks
  - `ui/state.py`: typed state; `UIState` translates to scenario dict.
  - `ui/components/`: `runspecs_form`, `constants_editor`, `points_editor` with live frontend validation (permissible keys, increasing times).
  - `ui/services/validation_client.py`: list permissible keys and validate in‑memory scenarios.
  - `ui/app.py`: tabs wired; sidebar retains preset runner; log streaming and CSV preview.
- Success Criteria
  - Editing produces a scenario dict that validates successfully using backend helpers.
  - No changes to SD/ABM behavior; all code under `ui/` and minimal public helpers only.
- Tasks
  - Implement `AnchorClientAgent` with fields: sector, activation_time, state, `requirements` dict keyed by material, counters for projects.
  - Implement `act(t, round_no, step_no)` to:
    - Progress projects; when completed projects reach threshold and after `anchor_client_activation_delay_<sector>`, transition to ACTIVE.
    - Generate per-material requirements using initial→ramp→steady phase logic with per-sector parameters and material start years.
    - Apply per-sector `requirement_to_order_lag` by leaving timing to SD via gateway usage and sector lag at delivery aggregation step (see Phase 6/7).
  - Implement per-sector factories `AnchorClientAgent_<sector>` and a registry keyed by sector.
- Success Criteria
  - Deterministic per-agent requirement streams given fixed parameters.
  - No randomness or hidden defaults inside agents; all behavior driven by sector parameters.
- Testing
  - Unit tests for agent phase transitions and requirement generation over a small timeline.
  - Determinism test: repeated runs with identical inputs produce identical per-step outputs.
- Debugging
  - Add DEBUG logs in first N steps showing state changes and per-material requirements for a few agents.

## UX Phases 6–8 — Primary Map, Seeds, Validate & Save (Streamlit)
- Scope
  - Extend the UI (kept isolated under `ui/`) to support editing `overrides.primary_map` and `seeds`, validating the full scenario in‑memory, and saving YAML to `scenarios/`.
- Tasks
  - `ui/components/primary_map_editor.py`: sector selector, current mapping preview, proposed mapping builder (materials multi‑select + per‑material `start_year`).
  - `ui/components/seeds_editor.py`: tabs for anchor sector seeds (hidden in SM‑mode), SM seeds editor (shown only in SM‑mode), and direct client seeds per material.
  - `ui/state.py`: add `PrimaryMapState`, `SeedsState`, update `UIState` assembly to include `overrides.primary_map` and `seeds`.
  - `ui/services/builder.py`: add `write_scenario_yaml(scenario_dict, dest_path)` with safe directory handling.
  - `ui/app.py`: new tabs Primary Map, Seeds, Validate & Save. Validate via `src.scenario_loader.validate_scenario_dict`; warn on overwrite.
- Success Criteria
  - UI can assemble scenarios including runspecs, constants, points, primary map, and seeds; validation errors surface inline; YAML written under `scenarios/`.
  - Model/runner behavior untouched; only `ui/` and public helpers used.
- Testing
  - Unit: temporary tests validate assembled scenario with primary map + seeds; YAML writer smoke tested.
- Exit criteria
  - Phases 3–8 fully operable from the UI: edit → validate → save; CLI runner remains the same.

## UX Phases 9–11 — Runner Integration, Presets, Docs (Streamlit)
- Scope
  - Add sidebar controls to run presets and run the current scenario (validate+save+run).
  - Stream logs into a panel and display the latest KPI CSV preview.
  - Preset manager to load/duplicate scenarios from `scenarios/`.
- Tasks
  - `ui/services/builder.py`: process control, log tail helpers, scenario IO utilities (`read_scenario_yaml`, `list_available_scenarios`).
  - `ui/state.py`: `load_from_scenario_dict` to populate editor from YAML.
  - `ui/app.py`: integrate run-current flow, log polling, CSV preview, preset load/duplicate UI.
- Success Criteria
  - End-to-end flow from edit → validate → save → run via the GUI.
  - No changes to model/runner beyond public helpers already introduced.

## Phase 6 — ABM→SD Gateways & Sector Anchor Deliveries
- Tasks
  - For each sector–material pair, create SD converter `Agent_Demand_Sector_Input_<s>_<m>`; compute `Agent_Aggregated_Demand_<m> = sum_s Agent_Demand_Sector_Input_<s>_<m>`; wire `Total_Demand_<m> = Agent_Aggregated_Demand_<m> + Client_Requirement_<m>`.
  - Compute anchor deliveries per sector with sector–material specific order lag L_{s,m} using SD constructs:
    - `Delayed_Agent_Demand_<s>_<m> = Agent_Demand_Sector_Input_<s>_<m> * Fulfillment_Ratio_<m>`
    - `Anchor_Delivery_Flow_<s>_<m> = delay(model, Delayed_Agent_Demand_<s>_<m>, requirement_to_order_lag_<s>_<m>)`
    - `Anchor_Delivery_Flow_<m> = sum_s Anchor_Delivery_Flow_<s>_<m>`
- Success Criteria
  - Gateways accept numeric equations and can be updated each step without re-compilation.
  - `Anchor_Delivery_Flow_<m>` reflects both lags and capacity via `Fulfillment_Ratio_<m>`.
- Testing
  - Integration test: inject synthetic agent demand and verify deliveries after the correct lag with capacity capping.
- Debugging
  - DEBUG print first N steps of `Agent_Demand_Input_<m>`, `Total_Demand_<m>`, `Fulfillment_Ratio_<m>`.

## Phase 7 — Stepwise Runner & Scheduler Integration
- Tasks
  - Initialize model with `runspecs`; apply scenario overrides (constants/points) strictly by element name.
  - Per step:
    - Read `Agents_To_Create_<s>` to determine integer agents to instantiate via sector factory.
    - Call `act(...)` on all agents.
    - Aggregate per-sector–material requirements across agents; set `Agent_Demand_Sector_Input_<s>_<m>` numeric equations accordingly.
    - Advance the SD model one step using the BPTK_Py scheduler.
    - Capture required outputs for this time index.
  - Ensure ordering and immutability guarantees inside the loop.
- Success Criteria
  - End-to-end run completes for baseline scenario; outputs cover exactly 28 quarters with correct labels.
  - Internal identity holds each step: `Total_Revenue ≈ sum_m(Anchor_Revenue_<m> + Client_Revenue_<m>)`.
- Testing
  - Integration test with minimal scenario and mocked agent creation (fixed known numbers) to check scheduler stepping.
  - Performance smoke: full horizon < 5 seconds for provided dataset on a laptop.
- Debugging
  - INFO logs for run start/stop, step counters; DEBUG for step snapshots gated by a flag.

## Phase 8 — KPI Extraction & CSV Writer
- Tasks
  - Map model elements to output rows exactly as specified (e.g., `Revenue`, `Revenue <sector>` where sector revenue is anchor-only, `Revenue <material>` which is anchor+direct, `Anchor Leads`, `Other Clients <material>`, `Order Basket <material>`, `Order Delivery <material>`).
  - Generate 28-quarter labels `YYYYQn` starting from starttime.
  - Write `output/FFF_Growth_System_Complete_Results.csv` with strict ordering and complete coverage; fill truly missing series with zeros only if the corresponding element is not applicable, otherwise treat as error.
  - Provide per-step ABM metrics (`agent_metrics_by_step`) to the extractor to compute agent-based KPI rows (Anchor Clients, Active Projects). This is mandatory; there is no fallback. If you cannot compute ABM metrics, construct and pass a zero-initialized list of length equal to emitted steps so ABM rows emit as zeros.
- Success Criteria
  - CSV matches expected shape: 1 label + 28 periods; deterministic across runs with same inputs.
  - Cross-check: `Order Delivery <m>` equals `Anchor_Delivery_Flow_<m> + Client_Delivery_Flow_<m>` per quarter.
- Testing
  - Golden file comparison against `Inputs/Expected Output.csv` if provided for a baseline scenario.
  - Unit tests for quarter labeling and series extraction alignment.
- Debugging
  - Summarize any missing element names; list non-applicable vs. missing distinctly.

## Phase 9 — Logging, Validation, and Error Policy
- Tasks
  - Scenario echo: write applied overrides to `logs/` and console.
  - Step-level gateway sampling: log selected materials for first 4–6 steps, mid-run, and last step.
  - Validation checks: fulfillment ratio in [0,1], integer agent creation non-negative, revenue identity per step.
- Success Criteria
  - Runs produce concise INFO logs and optional detailed DEBUG logs; no warnings remain unresolved.
  - Streamlit UI can show run logs (tailed from `logs/run.log`) and preview KPI CSVs.
- Testing
  - Unit tests for validation utilities (bounds checks, identity check function).
- Debugging
  - On any failed validation, stop the run with an actionable message and a snapshot dump of relevant values.

## Phase 10 — Test Suite & Regression Scenarios
- Tasks
  - Unit tests: naming, CSV parsing, scenario overrides, agent lifecycle, gateway updates, lookups and delays, scheduler integration, runner smoke E2E, and sensitivity tests.
  - Integration tests: small synthetic scenarios with hand-computable outputs.
  - Regression: baseline scenario pinned; compare KPIs to a blessed CSV to detect drift.
- Success Criteria
  - All tests green locally; CI-ready.
  - UI helper tests validate scenario assembly and YAML writer; builder utilities covered.
- Debugging
  - On failures, print minimal diffs of numeric series and the first mismatching time index.


---

## Implementation Guidelines & Patterns
- Modularity
  - Separate modules: data ingestion, naming, scenario loader, sd_model, agents, runner, kpi_extractor, io.
  - Functions with narrow responsibilities; no cross-cutting implicit state.
- Naming & Types
  - Use descriptive function and variable names; avoid abbreviations; keep explicit types in public interfaces where applicable.
- SD-DSL Usage (BPTK_Py)
  - Use standard SD elements: Stocks, Flows, Converters, Constants, Lookup Tables, `delay` and `lookup` equations.
  - Keep equations static; only gateway converter numeric values change per step.
- Delays & Units
  - All delays/durations expressed in quarters and passed directly to SD `delay` constructs; do not multiply by dt.
- Strict Input Policy
  - No default parameter values; missing data is a hard error with a precise message.

---

## Acceptance Checklist (Go/No-Go)
- Data completeness: all required sector/material parameters present and numeric.
- Model build: all elements enumerated in the technical architecture exist and compile.
- Scenario application: overrides applied by exact element name with zero unresolved keys.
- Stepwise run: deterministic loop order; runtime within expected bounds.
- Outputs: 28 quarters, correct labels, KPI identity checks pass, revenue identity holds per step.
- Tests: unit + integration + regression green.
- No hardcoded defaults, no fallbacks, no silent coercions.



---

## Feature Expansion Plan (Phases 11–15): Scenario Variants, Visualization, Multi‑Material Anchors, Seeded Starts, Variable Horizon

This section specifies the incremental delivery of the five requested capabilities. Each phase is self‑contained, minimizes blast radius, and adheres to strict inputs‑only policy (no defaults, no fallbacks). Where relevant, BPTK_Py SD‑DSL primitives are referenced: Converters, Stocks, Flows, Lookup Tables, `lookup(time, table)`, `delay(model, x, tau)`, and scheduler‑driven `run_step`.

### Phase 11 — Scenario Parameters & Toggles (Inputs‑only, strict validation)
- Scope
  - Enhance scenario handling to make parameter toggling first‑class: constants and lookup points for all sectors/materials.
  - Add CLI ergonomics for selecting scenario files and optional presets that resolve to explicit YAML/JSON files. Presets are not implicit defaults; they are concrete files in `scenarios/`.
- Tasks
  - `simulate_fff_growth.py`:
    - Support `--preset <name>` mapping to files under `scenarios/` (mutually exclusive with `--scenario <path>`). Default remains `scenarios/baseline.yaml`.
    - After writing the default KPI CSV, also write a suffixed copy `FFF_Growth_System_Complete_Results_<scenario>.csv` to enable side‑by‑side comparisons. This does not change KPIs or model behavior.
  - `src/scenario_loader.py`:
    - Strengthen validation: every override key must match an existing element name created by the model. Unknown keys ⇒ hard error with nearest‑name suggestions; do not apply partials.
    - Enforce strictly numeric constants and points; sort points by time and fail on non‑numeric or unsorted when ambiguous.
    - Add a helper to validate overrides against the built model before applying.
    - Echo applied overrides to `logs/scenario_overrides_echo.yaml`.
  - Documentation: examples for “high-capacity”, “price-shock”.
- Success criteria
  - Running with different scenario files produces different, deterministic outputs with changes traceable to explicit override deltas in logs.
  - Suffixed CSVs are written alongside the default without altering KPI logic.
  - No hidden defaults; missing inputs cause a clear validation error pointing to the exact key.
- Testing
  - Unit: unknown constant key ⇒ error; malformed points ⇒ error; sorted points applied verbatim.
  - Integration: run baseline vs. price‑shock; assert price‑sensitive KPIs differ in expected direction.
- Debugging
  - Log block of the exact set of applied constants/points; include counts of overridden vs. total elements.

### Phase 12 — Visualization (Read‑only; post‑processing of CSV) and Packaging
- Scope
  - Create a plotting module that reads `output/FFF_Growth_System_Complete_Results.csv` and generates static PNGs (optionally HTML later) without touching SD/ABM logic.
- Tasks
  - Add `viz/plots.py` with functions:
    - `plot_revenue_total_and_by_sector(df)` (total + sector-only)
    - `plot_revenue_by_material(df)`
    - `plot_leads_and_clients(df)` (Anchor Leads, Other Leads, Other Clients)
    - `plot_order_basket_vs_delivery(df)` per material and totals
    - `plot_capacity_utilization(df)` if utilization is present or derivable
  - `simulate_fff_growth.py`: optional `--visualize` flag to invoke plots after a run; images saved under `output/plots/` with deterministic filenames.
  - Handle dynamic quarter labels directly from CSV header; no assumptions about 28 quarters (future‑proofing for Phase 15).
  - Packaging: add `Makefile` targets (`install`, `test`, `run_ui`, `run_baseline`) and optional `Dockerfile.ui` to containerize the UI only (mount `scenarios/`, `logs/`, `output/`).
- Success criteria
  - Running with `--visualize` creates PNGs for all required plots; files exist and are non‑empty; time axes match CSV labels exactly.
  - Visualization is read-only; SD/ABM behavior and CSV contents are unchanged by plotting. Packaging enables one-command local start and optional container start.
- Testing
  - Smoke test: generate plots on baseline; assert files created and readable by PIL/matplotlib with no exceptions. Builder/State round-trip tests added to harden UI edge cases.
  - Keep full test suite green; plotting test skips if CSV is absent.
- Debugging
  - On missing rows/columns, print the missing label names and exit non‑zero; do not silently substitute zeros.

### Phase 13 — Multi‑Material Anchors (extend sector→materials mapping) and Hardening
- Scope
  - Allow each sector to drive requirements for multiple materials. SD side already supports per sector–material gateways; extend inputs and KPI enumeration.
- Tasks
  - `inputs.json`: extend `primary_map` entries to include multiple materials per sector with `StartYear` per mapping.
  - `src/phase1_data.py`: validate that for every (sector, material) mapping, the material exists in other tables and `StartYear` is numeric (warn only if ≤ 0 per current policy).
  - `src/fff_growth_model.py`:
    - Ensure creation of `Agent_Demand_Sector_Input_<s>_<m>` for every mapped pair.
    - Ensure `Anchor_Delivery_Flow_<s>_<m>` contributes to `Anchor_Delivery_Flow_<m>` and sector revenue aggregation.
  - `src/kpi_extractor.py`:
    - Enumerate KPI rows for any new materials and maintain sector/material sums: `Revenue <m>` = `Anchor_Revenue_<m> + Client_Revenue_<m>`, `Revenue <s>` = sum over materials’ sector revenues.
- Success criteria
  - When mapping adds materials to a sector, CSV gains the corresponding rows; totals by material and sector reconcile every quarter.
  - No rows emit for unmapped pairs.
  - Verified via scenario `scenarios/multi_material_defense_aviation.yaml` and programmatic CSV checks: new material (Silicon Nitride Fiber) shows zero deliveries before 2026 and first non‑zero at 2027Q2 due to sector lag; `Revenue Defense` increases commensurately. Aviation with `Boron_fiber` mapped similarly.
- Testing
  - Unit: mapping validation (presence, numeric `StartYear`).
  - Integration: a crafted scenario where one sector maps two materials with distinct lags/capacity; assert delivery timing and revenue attribution per sector–material and aggregation identities.
  - UI hardening: tests for `ui.services.builder.build_runner_command` and `ui.state` round‑trip to guard packaging and editor flows.
- Debugging
  - DEBUG snapshot for first few steps: per sector–material gateway values, fulfillment ratio, and anchor delivery flow; include step timestamps.

### Phase 14 — Seeded Starting Inputs (pre‑existing anchors at t0)
- Scope
  - Allow scenarios to seed active anchor clients at t0 per sector, fully input‑driven. No inferred defaults; zero seeding unless explicitly specified.
- Tasks
  - Scenario schema: add `seeds.active_anchor_clients: { <sector>: <int> }` and (optional) `seeds.elapsed_quarters: { <sector>: <int> }` if advanced phase seeding is desired later.
  - `src/scenario_loader.py`: validate integers ≥ 0; sectors must exist; store seeds in scenario object (`seeds_active_anchor_clients`, optional `seeds_elapsed_quarters`).
  - Runner (`simulate_fff_growth.py`):
    - Instantiate the exact number of ACTIVE agents per sector before the first step. If `elapsed_quarters` is provided, set `activation_time_years = starttime - elapsed_quarters*dt` so phase logic ages accordingly at step 0.
    - Ensure seeded agents generate requirements at step 0 but respect sector–material start years.
    - Initialize SD stocks for gating/monitoring: `CPC_<sector> = seeds` (conservative mapping to include seeds in ATAM gating) and `Cumulative_Agents_Created_<sector> = seeds`. Log any elements that cannot be initialized (non-fatal).
  - `src/kpi_extractor.py`: existing stepwise capture uses runner-provided `agent_metrics_by_step`; seeded counts appear at step 0 without further changes.
- Success criteria
  - With seeds configured, step‑0 KPIs reflect active counts; requirements and deliveries follow from seeded agents respecting sector–material start years and lags. ATAM gating includes seeded clients via `CPC_<sector>` initialization.
- Testing
  - Unit: scenario validation for seeds; agent factory creates ACTIVE agents with expected initial state.
  - Integration: compare runs with and without seeds; assert non‑zero early requirements/deliveries only for seeded sectors/materials after appropriate lags.
- Debugging
  - DEBUG: log seed instantiation per sector (counts) and first‑step per‑material requirements from seeded agents.

### Phase 15 — Variable Time Range (generalized horizon)
- Scope
  - Make start/end/dt fully scenario‑driven, and propagate to labeling and extraction. Remove any fixed 2025–2031 assumptions from output.
- Tasks
- `src/scenario_loader.py`: already supports arbitrary numeric `starttime`, `stoptime`, `dt` with strict validation (`stoptime > starttime`, `dt > 0`).
- `simulate_fff_growth.py`: uses the runspecs grid to construct `num_steps` and iterate; captures KPIs in real time and scales per‑year lead signals to per‑step units by multiplying by `dt`.
- `src/kpi_extractor.py`:
  - Labels are generated from the time grid (`starttime`, `dt`, `num_steps`); exactly one column per simulated step is emitted.
  - Fallback evaluation path remains for testing, but production uses runner‑captured values for gateway‑dependent KPIs; no fixed 28 logic remains.
- Lookup tails: policy is hold‑last‑value beyond defined points. The runner emits WARN logs when time is below the first point or above the last point for any capacity/price lookup encountered at a step.
- Success criteria
  - Changing runspecs yields CSVs with variable numbers of period columns; labels match the time grid exactly. All tests pass for multiple horizons.
- Testing
  - Unit/Integration updated: the KPI extractor tests now expect `1 + num_steps` columns instead of a fixed 28. E2E and plotting continue to pass; short (2025–2029) and long (2025–2035) scenarios verified.
- Debugging
  - On label/grid mismatches, computed labels derive from grid; extrapolation now logs which lookup and time range was extrapolated per step.

### Cross‑cutting Policies (applies to Phases 11–15)
- Inputs‑only
  - No fallback mechanisms or simplifications. Every parameter and seed must come from `inputs.json` or an explicit scenario file. If missing, fail with a precise error.
- BPTK_Py SD‑DSL usage
  - Keep equations static; only gateway converter numeric values change per step via the runner. Use `lookup` and `delay` exactly as per library semantics with τ in quarters; do not scale τ by `dt`.
- Logging & Observability
  - INFO logs for high‑level milestones; DEBUG snapshots for first/mid/last steps with gateway values and key flows.
- Linting & Style
  - Run `python make_lint.py` as part of CI/local pre‑commit; prohibit unrelated reformatting.

---

## Phase 16 — Anchor Sector‑Material (SM) Parameters and SM Lists

### Scope
- Introduce full per‑(sector, material) parameters for Anchor (not for Direct Clients). Direct Clients remain material‑driven as before.
- Establish explicit SM lists (the universe of (s,m) pairs) to back per‑(s,m) inputs and validation. Initial SM list can be derived from the existing `primary_map` as a best‑guess starting point.

### Rationale
- Today, most anchor parameters are sector‑only while deliveries are realized per (s,m) via SD. This change lets us specify phase requirement parameters and anchor order lag at (s,m) granularity where needed, while preserving sector‑only and material‑only data where appropriate.

### Inputs (new/updated)
- `inputs.json` (new section)
  - `anchor_params_sm`: nested mapping param → sector → material → value.
    - Targeted per‑(s,m) params (initial set):
      - `requirement_to_order_lag`
      - `initial_requirement_rate`, `initial_req_growth`
      - `ramp_requirement_rate`, `ramp_req_growth`
      - `steady_requirement_rate`, `steady_req_growth`
    - Sector‑only params that remain sector‑level (unchanged):
      - leads and project lifecycle: `anchor_lead_generation_rate`, `lead_to_pc_conversion_rate`, `project_generation_rate`, `max_projects_per_pc`, `project_duration`, `projects_to_client_conversion`, `anchor_client_activation_delay`, `ATAM`, `anchor_start_year`.
- `inputs.json` (new/clarified)
  - `lists_sm`: optional explicit SM list with rows like `{ "Sector": "Defense", "Material": "Silicon Carbide Fiber" }`.
    - If absent, derive SM pairs from `primary_map` for this phase.

### Tasks
- Naming utilities (`src/naming.py`)
  - Add `anchor_constant_sm(param, sector, material)` helper to produce canonical names for per‑(s,m) constants (e.g., `requirement_to_order_lag_Defense_Silicon_Carbide_Fiber`).
- Phase 1 parsing & validation (`src/phase1_data.py`)
  - Parse `anchor_params_sm` into a normalized long table with columns [Sector, Material, Param, Value].
  - Add `lists_sm` support: either parse explicit list or compute from `primary_map` as initial universe.
  - Extend `Phase1Bundle` with `anchor_sm` and `lists_sm`.
  - Validation:
    - Ensure any (s,m) entries reference existing sectors/materials.
    - Fallback policy enforced in build (no hard requirement that all (s,m) params be present).
- Scenario loader (`src/scenario_loader.py`)
  - Expand permissible constants to include per‑(s,m) names generated via `anchor_constant_sm` for targeted params across the SM universe (from `lists_sm` or `primary_map`).
  - Maintain strict key validation and nearest‑match hints.
- SD model build (`src/fff_growth_model.py`)
  - Create constants per (s,m) for targeted params with precedence: (s,m) value if provided, else sector-level.
  - Use `requirement_to_order_lag_<s>_<m>` in anchor deliveries; it always exists after build (value from (s,m) or sector fallback).
  - No changes to capacity/price (material‑level) or direct‑client SD structure.
- ABM (`src/abm_anchor.py`)
  - Extend sector factory to pull per‑(s,m) requirement phase params for each mapped material.
  - Update `AnchorClientAgent` to use material‑specific phase params (initial/ramp/steady rate/growth) when ACTIVE via optional per-material maps.
  - Keep leads and project lifecycle sector‑level.
- Scenario overrides application (`apply_scenario_overrides`)
  - Existing by‑name constant assignment works once (s,m) constants exist; ensure tests cover (s,m) override cases.

### Compatibility & Precedence
- Fallback policy (strict and explicit): for each targeted per‑(s,m) parameter at pair (s,m):
  1) Use the per‑(s,m) value if provided.
  2) Else use the sector‑only value (for phase params, use sector baseline).
  3) Else raise a validation error naming the missing (s,m) parameter.
- Direct clients remain material‑level; no change to their inputs in this phase.

### Success Criteria
- Providing per‑(s,m) parameters modifies deliveries and revenues only for those pairs; sector‑only behavior matches legacy when per‑(s,m) values are absent.
- Validation catches missing or mis‑keyed (s,m) inputs with actionable messages.
- Scenario overrides can target specific (s,m) constants and take effect immediately.

### Testing
- Unit: parsing of `anchor_params_sm`; name generation; precedence resolution.
- Integration: crafted scenario where one sector maps two materials with distinct per‑(s,m) phase parameters and lags; verify timing and magnitudes.
- Regression: legacy scenarios (with no `anchor_params_sm`) continue to run identically.

### Debugging
- Log the discovered SM list (first N rows) and counts (pairs, params) at INFO.
- On validation error, include the exact (sector, material, param) triple missing.

### Data Initialization (best‑guess SM lists)
- For this phase, derive `lists_sm` from `primary_map` (all (s,m) pairs present in mapping). This keeps effort low and aligned with current usage.
- Populate `anchor_params_sm` minimally for targeted pairs where differentiation is needed; rely on sector‑level fallback otherwise.

## Phase 17 — SM‑mode (Global Per‑(Sector, Material) Control)

This phase family enables a global “SM‑mode” where all anchor pipeline parameters become per‑(sector, material). When enabled, there are no fallbacks or simplifications: every targeted parameter must be present for every (s,m) pair, and sector‑level creation is disabled. Legacy sector‑mode remains available and unchanged.

### Phase 17.1 — Schema, Naming, and Loader (strict, no fallbacks)
- Scope
  - Introduce a global mode switch and enforce complete per‑(s,m) coverage for all anchor parameters when SM‑mode is active.
- Tasks
  - Scenario schema
    - Add `anchor_mode: "sm" | "sector"` under `runspecs` (default: `"sector"`).
    - Add `seeds.active_anchor_clients_sm: { <Sector>: { <Material>: <int> } }` for SM‑mode seeding.
  - Inputs (`inputs.json`)
    - Extend `anchor_params_sm` to support the full anchor set per (s,m):
      - anchor_start_year, anchor_client_activation_delay, anchor_lead_generation_rate, lead_to_pc_conversion_rate,
        project_generation_rate, max_projects_per_pc, project_duration, projects_to_client_conversion,
        initial_phase_duration, ramp_phase_duration, ATAM,
        initial_requirement_rate, initial_req_growth, ramp_requirement_rate, ramp_req_growth,
        steady_requirement_rate, steady_req_growth, requirement_to_order_lag.
    - Require `lists_sm` (array of rows `{Sector, Material}`) as the SM universe when SM‑mode is active. No derivation from `primary_map` in SM‑mode.
  - Naming (`src/naming.py`)
    - Use `anchor_constant_sm(param, sector, material)` for all per‑(s,m) constants.
    - Add helpers for per‑(s,m) SD creation signals in 17.2 (if not already present) using `create_element_name`.
  - Loader (`src/phase1_data.py`, `src/scenario_loader.py`)
    - Validate `anchor_mode` ∈ {"sm","sector"}.
    - When `anchor_mode = "sm"`:
      - Require `lists_sm` non‑empty and consistent with `lists`.
      - Require `anchor_params_sm` to contain every targeted parameter for every pair in `lists_sm`.
      - Validate `seeds.active_anchor_clients_sm` integers ≥ 0 for pairs in `lists_sm`.
      - Strict overrides: only per‑(s,m) constants accepted for anchor parameters; unknown keys are hard errors.
- Success Criteria
  - SM‑mode refuses to load unless all targeted per‑(s,m) parameters and seeds (when present) are complete.
  - Sector‑mode behavior unchanged.
- Testing
  - Unit: schema toggles; complete vs. partial `anchor_params_sm`; `lists_sm` presence and coverage; `seeds_sm` typing and referencing.
  - Unit: permissible constants surface includes per‑(s,m) only in SM‑mode for anchor parameters.
- Debugging
  - Log counts at INFO: pairs, targeted parameters, coverage (e.g., `112/112 ok`).
  - On failure, print first N missing (sector, material, param) triples.

### Phase 17.2 — SD Model: Per‑(s,m) Creation Pipelines (no sector creation in SM‑mode)
- Scope
  - Build one creation pipeline per (s,m) pair; do not build sector‑level creation when SM‑mode is active.
- Tasks (BPTK_Py SD‑DSL)
  - For each (s,m) in `lists_sm` create:
    - Constants for all per‑(s,m) anchor parameters listed in 17.1.
    - Lead generation and PC conversion:
      - `Anchor_Lead_Generation_<s>_<m> = 4 * anchor_lead_generation_rate_<s>_<m> * If(Time ≥ anchor_start_year_<s>_<m>, 1, 0) * If(CPC_<s>_<m> < ATAM_<s>_<m>, 1, 0)`
      - `CPC_<s>_<m>` stock integrates the converter above.
      - `New_PC_Flow_<s>_<m> = Anchor_Lead_Generation_<s>_<m> * lead_to_pc_conversion_rate_<s>_<m>`
    - Accumulate‑and‑fire integerization (quarter‑correct):
      - `Agent_Creation_Accumulator_<s>_<m>` stock
      - `Agent_Creation_Inflow_<s>_<m> = New_PC_Flow_<s>_<m>`
      - `Agent_Creation_Outflow_<s>_<m> = max(0, Round(Agent_Creation_Accumulator_<s>_<m> - 0.5, 0))`
      - `Agent_Creation_Drain_<s>_<m> = 4 * Agent_Creation_Outflow_<s>_<m>`
      - `Agents_To_Create_<s>_<m> = Agent_Creation_Outflow_<s>_<m>`
      - `Cumulative_Agents_Created_<s>_<m>` stock with inflow `Agent_Creation_Drain_<s>_<m>`
  - Exclusivity: When `anchor_mode = "sm"`, do not create any sector‑level creation elements.
  - Deliveries side remains per‑(s,m) using `requirement_to_order_lag_<s>_<m>` as already implemented.
- Success Criteria
  - Model compiles with per‑(s,m) creation signals for all pairs; sector‑level creation is absent in SM‑mode.
- Testing
  - Unit: element presence and equations for a sample pair; integerization via Round works as expected.
  - Integration: multiple pairs build; no sector‑level creation in SM‑mode.
- Debugging
  - DEBUG snapshot (first 2–3 pairs): `Anchor_Lead_Generation`, `CPC`, `Agents_To_Create` at early steps.

### Phase 17.3 — ABM Per‑(s,m) Agent and Factories
- Scope
  - Introduce `AnchorClientAgentSM` bound to a single (sector, material) with a self‑contained lifecycle.
- Tasks
  - Implement `AnchorClientAgentSM` with states POTENTIAL → PENDING_ACTIVATION → ACTIVE.
  - Use per‑(s,m) lifecycle params: `project_generation_rate`, `max_projects_per_pc`, `project_duration`, `projects_to_client_conversion`, `anchor_client_activation_delay`, phase durations, and per‑(s,m) requirement phase parameters.
  - Respect `anchor_start_year_<s>_<m>` gating and generate requirements only when ACTIVE.
  - Provide `build_sm_agent_factory(sector, material)` returning fresh SM agents.
- Success Criteria
  - Deterministic requirements per step; no sector‑level values referenced when in SM‑mode.
- Testing
  - Unit: lifecycle transitions, activation timing, phase behavior with per‑(s,m) params.
  - Determinism test: identical outputs across repeated runs.
- Debugging
  - DEBUG per‑step log (opt‑in) for a sample agent: in‑progress projects and requirements.

Implementation status
- Implemented `AnchorClientAgentSM` bound to a single (sector, material) with POTENTIAL → PENDING_ACTIVATION → ACTIVE lifecycle and phase‑based requirements gated by `anchor_start_year_<s>_<m>`.
- Implemented `build_sm_anchor_agent_factory(sector, material)` sourcing parameters strictly from `anchor_params_sm` (no sector fallbacks in SM‑mode).
- Added unit tests for lifecycle timing, deterministic requirements, and strict factory sourcing in `tests/test_phase17_sm_mode.py`.

### Phase 17.4 — Runner Wiring: SM Instantiation, Seeding, Loop
- Scope
  - Switch the runner to use per‑(s,m) creation signals and SM agents when SM‑mode is active.
- Tasks
  - Step loop (SM‑mode):
    - Evaluate `Agents_To_Create_<s>_<m>` and instantiate via `build_sm_agent_factory`.
    - Call `.act(...)` on all SM agents; aggregate their single‑material requirements into `Agent_Demand_Sector_Input_<s>_<m>`.
  - Seeding (SM‑mode only):
    - `seeds.active_anchor_clients_sm[sector][material]` → create that many ACTIVE SM agents at t0.
    - Initialize SD stocks: `CPC_<s>_<m> = seeds_sm` and `Cumulative_Agents_Created_<s>_<m> = seeds_sm` if elements exist; log non‑fatals otherwise.
  - Prohibit legacy sector‑level seeding in SM‑mode (raise if both present).
- Success Criteria
  - End‑to‑end SM‑mode run completes; KPIs produced; per‑(s,m) seeds visible at step 0.
- Testing
  - Integration: 2×2 pairs with distinct pre‑activation params; verify differing creation timing/activation and requirement streams.
  - Seeding: verify step‑0 metrics and initial SD stock values for seeded pairs.
- Debugging
  - INFO: mode, pair counts, seeds summary. DEBUG: early/mid/late snapshots for a small subset of pairs.

Implementation status
- Runner switches to SM‑mode when `runspecs.anchor_mode == "sm"`, instantiating agents via `build_sm_anchor_agent_factory` using per‑(s,m) creation signals `Agents_To_Create_<s>_<m>`.
- SM‑mode seeding is supported via `seeds.active_anchor_clients_sm`, creating ACTIVE agents at t0 and initializing `CPC_<s>_<m>` and `Cumulative_Agents_Created_<s>_<m>` when elements exist. Sector‑level seeding remains prohibited in SM‑mode (enforced by loader).
- Per‑step aggregation writes `Agent_Demand_Sector_Input_<s>_<m>` for all mapped pairs with deterministic zeroing when absent.
- KPI capture sums per‑(s,m) `Anchor_Lead_Generation_<s>_<m>` when sector‑level `Anchor_Lead_Generation_<s>` is absent in SM‑mode to compute `Anchor Leads <sector>`.
- Validation added for SM creation signals: `validate_agents_to_create_sm_signals` ensures non‑negative integer `Agents_To_Create_<s>_<m>` each step.

### Phase 17.5 — Strict Enforcement (No Fallbacks, No Simplifications)
- Scope
  - Guarantee strict inputs‑only policy in SM‑mode.
- Tasks
  - Loader/model: require full per‑(s,m) coverage; raise on any missing (s,m,param). Implemented in `src/scenario_loader.py` (SM completeness + explicit `lists_sm`) and `src/fff_growth_model.py` (strict `_require_anchor_sm_value` paths when `runspecs.anchor_mode == "sm"`).
  - Scenario overrides: accept only per‑(s,m) anchor constants in SM‑mode. Implemented by mode-specific permissible constants surface in `src/scenario_loader.py`.
  - Mode exclusivity: deny sector‑level creation and seeding in SM‑mode. Implemented: sector-level creation not built in SM-mode; sector seeds rejected early in loader.
- Success Criteria
  - Any missing/extra/mixed inputs produce actionable errors before run. Verified via unit tests.
- Testing
  - Negative: partial `anchor_params_sm` → error; sector seeds in SM‑mode → error; unknown per‑(s,m) keys → error. Implemented in `tests/test_phase17_5_strict.py`.
- Debugging
  - Echo compliance counts; list first N issues precisely.

### Phase 17.6 — KPIs and Optional Granularity
- Scope
  - Keep KPI surface stable; optionally add granular per‑(s,m) diagnostics.
- Tasks
  - Default KPI mapping unchanged (sector/material totals intact).
  - Optional (flag): emit `Anchor Clients <sector> <material>` and/or `Revenue <sector> <material>`.
  - Implemented in `kpi_extractor.build_row_order` and runner KPI capture with CLI flags `--kpi-sm-revenue-rows` and `--kpi-sm-client-rows`.
- Success Criteria
  - Regression CSV shape unchanged by default; optional rows only when requested.
  - Optional rows populated when enabled; zero when not applicable.
- Testing
  - Golden regression unaffected; optional rows verified under flag via `tests/test_phase17_6_kpi_granular.py` (row order and presence checks).
- Debugging
  - Runner logs whether optional rows are enabled at start of loop and emits values accordingly.

### Phase 17.7 — Documentation, Examples, and Migration Aids
- Scope
  - Document SM‑mode thoroughly and provide runnable examples.
- Tasks
  - Docs: update `technical_architecture.md`, `systems_elements.md`, `inputs.md` with SM‑mode schema, element names, and exclusivity rules.
  - Examples: `scenarios/sm_minimal.yaml`, `scenarios/sm_full_demo.yaml` demonstrating distinct pre‑activation and phase dynamics per pair.
- Success Criteria
  - Examples run without errors; docs fully reflect SM‑mode rules.
- Testing
  - CI smoke: run examples with asserts on basic KPIs and structure.
- Debugging
  - Scenario echo includes SM parameters and seeds blocks for traceability.

Implementation status
- Docs updated: `technical_architecture.md`, `systems_elements.md`, `inputs.md` to document SM‑mode schema, strictness, and examples.
- Examples added: `scenarios/sm_minimal.yaml` and `scenarios/sm_full_demo.yaml` run successfully end‑to‑end and write KPI CSVs.
- Scenario echo enhanced to include `runspecs.anchor_mode` and `seeds` (including `active_anchor_clients_sm`).

### Phase 17.8 — Completed-Projects Seeding (Anchors)
- Scope
  - Allow scenarios to seed a backlog of completed projects at t0 for anchors in both modes.
- Tasks
  - Schema (sector mode): `seeds.completed_projects: { <sector>: <int> }`.
  - Schema (SM mode): `seeds.completed_projects_sm: { <Sector>: { <Material>: <int> } }`.
  - Loader: validate non-negative integers; enforce mode rules (sector key disallowed in SM-mode; pair keys must exist in `lists_sm`).
  - Runner: convert backlog deterministically per sector/pair:
    - `num_active = floor(completed / projects_to_client_conversion)` immediate ACTIVE anchors at t0 (threshold read from model constants so scenario overrides apply).
    - Apply remainder to a POTENTIAL agent’s completed counter for near-term activation.
    - Increase SD initial values for `CPC_*` and `Cumulative_Agents_Created_*` by `num_active` so ATAM gating/monitoring reflect added ACTIVE anchors.
- Success Criteria
  - With backlog configured, step-0 Anchor Clients reflect the floor division; remainder does not create an ACTIVE until subsequent steps.
  - ATAM gating honors additional active anchors via CPC initialization.
- Testing
  - Added regression tests asserting step-0 Anchor Clients for sector and SM cases with explicit per-agent thresholds.
- Docs
  - Updated `technical_architecture.md`, `tutorial.md`, and `index.md` to describe schema and behavior.

### Cross‑cutting Policies (SM‑mode)
- Inputs‑only; no fallbacks or defaults. Every targeted parameter and seed must come from `inputs.json` or the scenario; otherwise the run fails with a precise error.
- Static SD equations; only numeric gateway values change per step.
- Deterministic step order: instantiate → act → aggregate → set gateways → capture KPIs → advance scheduler.
- BPTK_Py SD‑DSL usage: use `If`, `Round(x-0.5,0)` for floor‑like integerization, `delay(model, x, τ)` (τ in quarters), and `lookup(time, points)`.
