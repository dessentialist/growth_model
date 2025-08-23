## Growth System – Technical Architecture (BPTK_Py Hybrid, Pattern 1)

### Purpose
Enable robust scenario planning for revenue and KPIs by aligning the model and runner with BPTK_Py’s hybrid SD+ABM capabilities. This architecture treats each Anchor Client as an agent, couples agent behavior to SD via a stepwise ABM→SD gateway, and externalizes scenario inputs in JSON/YAML. Single-scenario execution per run is prioritized for simplicity and reliability.

### Objectives & Scope
- **Objectives**: Scenario planning with tweakable exogenous/endogenous inputs; quarterly KPIs (revenue, leads, clients, deliveries, baskets, projects).
- **Scope**: Hybrid model (SD core + ABM for Anchor Clients) with stepwise coupling; scenario configs; deterministic CSV outputs; comprehensive logging.
- **Out of scope (initial)**: Multi-scenario batch runs; stochastic effects; interactive plotting. Phase 12 adds static, read-only plotting as post-processing of the CSV and packaging conveniences (Makefile, optional UI container).

## High-Level Design

### UI Architecture (Streamlit Layer)

- Goals: Thin, isolated UI that never mutates the model; use YAML + CLI only.
- Structure under `ui/`:
  - `ui/app.py`: Streamlit entrypoint with tabs for Runspecs, Constants, Points, Primary Map, Seeds, Validate & Save, and Run. Loads a cached `Phase1Bundle` once and delegates to components/services.
  - `ui/state.py`: Typed dataclasses for UI state and helpers to assemble/load scenario dicts.
  - `ui/components/`: Page fragments to edit specific sections and update `UIState`.
  - `ui/services/validation_client.py`: Calls `src.scenario_loader` helpers to list permissible keys and validate scenarios in-memory.
  - `ui/services/runner.py`: Runner integration (command build, spawn/terminate, efficient log tail, find latest CSV, optional plot generation). Pure process/IO, no Streamlit imports.
  - `ui/services/builder.py`: Scenario assembly and YAML IO. Backward-compatible re‑exports for runner helpers are provided but new code should import from `ui.services.runner`.
- Data flow:
  1) Load inputs (`Phase1Bundle`) → get permissible keys and lists
  2) User edits → build in‑memory `scenario_dict`
  3) Validate with `validate_scenario_dict`
  4) Save YAML to `scenarios/`
  5) Run CLI in subprocess → tail logs → preview KPI CSV (optional `--visualize`; UI renders `output/plots/*.png` inline when present)
- Isolation: UI uses only public helpers; runner executed as subprocess; no SD/ABM imports in components.
- Packaging: `Makefile` targets (`install`, `run_ui`, `run_baseline`, `test`, `lint`); optional `Dockerfile.ui` to containerize the UI (mount `scenarios/`, `logs/`, `output/`).

### Modeling Approach
- **Hybrid Pattern 1 (recommended)**: Predefine per-material gateway converters that accept numeric inputs each time step. The runner computes aggregated agent demand and sets gateway values before advancing the SD step.
- **Why this pattern**: Minimal intrusion, explicit data flow, easy logging and validation, and fully compatible with BPTK_Py’s deterministic SD equation evaluation.

### Core Components
- **System Dynamics (SD) Model**
  - Implements the spec in `spec_sheet.txt`: lead-gen, project conversion, requirement generation, capacity, fulfillment, and revenue.
  - Uses BPTK_Py stocks/flows/converters/lookup tables for time-continuous dynamics at dt = 0.25 (quarterly).

- **Agent-Based Model (ABM)**
  - `AnchorClientAgent` per sector; each agent has lifecycle and generates material-specific requirements according to three phases (initial, ramp, steady), activation delays, and sector-specific parameters.
  - Agents act each time step to update per-material requirements.
  - Phase 17.3 (SM‑mode ABM): `AnchorClientAgentSM` bound to a single (sector, material) with a self‑contained lifecycle (POTENTIAL → PENDING_ACTIVATION → ACTIVE). Factory `build_sm_anchor_agent_factory(sector, material)` constructs agents strictly from `anchor_params_sm` for the pair (no sector fallbacks). Requirements are generated only when ACTIVE and after `anchor_start_year_<s>_<m>`.

- **ABM→SD Gateway Converters (per sector–material)**
  - For each sector s and material m used by s, define a converter `Agent_Demand_Sector_Input_<s>_<m>` with a numeric equation (value set by runner each step).
  - Define `Agent_Aggregated_Demand_<m> = sum_over_sectors_s(Agent_Demand_Sector_Input_<s>_<m>)`.
  - `Total_Demand_<m> = Agent_Aggregated_Demand_<m> + Client_Requirement_<m>`
  - Capacity, deliveries, and revenue use `Total_Demand_<m>` while retaining sector attribution for anchor deliveries. Sectors may map to multiple materials; the model constructs `Agent_Demand_Sector_Input_<s>_<m>` and `Anchor_Delivery_Flow_<s>_<m>` for every mapped pair and aggregates by material and by sector for KPIs.

- **Scenario Configuration (JSON/YAML)**
  - One scenario file per run; provides constants and lookup overrides using exact model element names.
  - Runner supports `--preset <name>` to select files under `scenarios/`. Unknown override keys are strict errors with nearest-name suggestions; overrides are validated against built model elements before application (no partials). In SM‑mode (17.5 strictness), only per‑(s,m) anchor constants are permissible override keys for anchor parameters.
  - UI (Phases 3–11) builds an in‑memory scenario via tabs for runspecs, constants, points, primary map, and seeds; validates using `src.scenario_loader.validate_scenario_dict`; can write YAML to `scenarios/`; can load/duplicate scenarios; and can run either a named preset or the current scenario from the sidebar. The UI does not alter model logic; it is an isolated layer under `ui/`.
  - After a run, the runner writes the default CSV and an additional suffixed CSV `Growth_System_Complete_Results_<scenario>.csv` for cross-scenario comparisons. This does not change KPI logic or model state.

- **Stepwise Simulation Runner**
  - Initializes model, registers agent factories, builds SD structure, creates gateways, applies scenario overrides.
  - Executes a per-step loop: reads SD triggers, creates agents, runs agent actions, aggregates per-material demand, sets gateway converter values, advances SD one step using the scheduler (`run_step`), collects outputs.
  - SM-mode (Phase 17.4/17.5): per-(sector, material) creation signals `Agents_To_Create_<s>_<m>` drive instantiation via SM factories; SM seeding initializes `CPC_<s>_<m>` and `Cumulative_Agents_Created_<s>_<m>`; KPI capture sums `Anchor_Lead_Generation_<s>_<m>` when sector-level is absent. Strict rules: sector-level creation and seeding are disallowed in SM-mode; `lists_sm` must be explicit in `inputs.json`; full `anchor_params_sm` coverage is required for every pair.

## Data Inputs
- JSON-first (`inputs.json`) with strict validation:
  - Top-level `'lists'` is required; lists are reconstructed US-only in this phase and must include `'US'`.
  - `anchor_params` (per sector), `other_params` (per material), `production` (per material by year), `pricing` (per material by year), `primary_map` (sector→materials with start_year). Phase 16 adds optional `anchor_params_sm` (per-(sector, material) targeted parameters) and optional `lists_sm` (explicit SM universe; if absent, derived from `primary_map`).
  - Primary map entries with `start_year <= 0` are allowed but logged as warnings (treated as disabled).
  - Production/Pricing time series must have strictly increasing years and non-negative values.
  - SM‑mode (Phase 17.5): requires explicit `lists_sm` (not derived) and complete `anchor_params_sm` coverage for the full anchor set per pair listed in the implementation plan.

## Naming & Dimensions
- Use `create_element_name(base[, sector][, material])` to generate BPTK-compatible names: underscores for spaces, generous length limit (~100 chars) with hash-based truncation only if needed; detect collisions. Phase 16 adds `anchor_constant_sm(param, sector, material)` for per-(s,m) constants names (e.g., `requirement_to_order_lag_Defense_Silicon_Carbide_Fiber`).
- Names should remain stable across runs so scenarios can reliably override elements.

## SD Structure (essential elements)
- Anchor lead-gen per sector: `Anchor_Lead_Generation_<sector>`, `CPC_<sector>`, `New_PC_Flow_<sector>`.
- Project conversion per sector using “accumulate-and-fire” logic; activation delays drive AC activation.
- Direct client submodel per material: leads → discrete clients → requirements (with delays) → fulfillment.
- Capacity per material via `max_capacity_lookup_<material>` converter (lookup on `max_capacity_<material>(Time)`).
- Total demand per material: `Total_Demand_<material> = Agent_Demand_Input_<material> + Client_Requirement_<material>`.
- Fulfillment ratio, delivery flows:
  - `Anchor_Delivery_Flow_<material>` (delayed, capacity-constrained sum of sector agent demands).
  - `Client_Delivery_Flow_<material>` (delayed, capacity-constrained client fulfillment).
- Revenue: `Price_<material> = lookup(price_<material>, Time)`, then `Anchor_Revenue`, `Client_Revenue`, `Total_Revenue`.

## ABM Structure (essential elements)
- `AnchorClientAgent` properties: sector, parameters, `primary_materials`, `state`, per-material `requirements`, `activation_time`, project counters.
- `act(time, round_no, step_no)`: complete due projects, start projects if eligible, switch to ACTIVE when threshold met, generate requirements by phase for relevant materials.
- Per-step outputs used by runner to aggregate requirements by material.
- Phase 17.3: `AnchorClientAgentSM` properties: sector, material, strict per‑(s,m) params, lifecycle state, activation time, project counters; `act(...)` updates a single-material requirement per step with initial/ramp/steady phases.

## System Logic Overview (plain language)

This captures the business intent without technical details:

- Structure
  - Markets contain sectors; each sector uses one or more primary materials starting in specific years.
  - Two channels: Anchor clients (sector-specific, agent-based) and Other clients (material-specific, aggregated SD).

- Anchor clients (per sector, per client)
  - Leads are generated at a sector rate, capped by an addressable limit (ATAM). Leads accumulate to Potential Clients (PC).
  - PCs start projects up to a max projects-per-PC; projects complete after a duration.
  - When completed projects reach a threshold, the PC becomes an Active Client after an activation delay.
  - Active clients generate requirements for the sector’s primary materials in three phases (initial, ramp, steady) with configurable rates/growth and material start years.

- Other (direct) clients (per material)
  - Inbound and outbound leads accrue, capped by a material TAM.
  - Discrete client creation uses accumulate-and-fire (only whole clients are created).
  - Clients place orders with an average quantity that grows over time; requirements convert to orders via a lead-to-requirement delay and are fulfilled after a fulfillment delay.

- Demand aggregation and fulfillment
  - Total demand per material = Anchor agent demand (sum across sectors) + Direct client requirements.
  - Each material has a time-varying capacity; fulfillment uses a proportional ratio across channels by default.
  - Anchor orders use sector–material specific requirement-to-order lags; direct client orders include fulfillment delays.

- Pricing & Revenue
  - Material prices vary over time.
  - Quarterly revenue = deliveries × price; computed for Anchor and Direct, then summed.

- KPIs (quarterly)
  - Revenue (total, by sector, by material)
  - Anchor Leads, Anchor Clients, Active Projects
  - Other Leads (total and by sector via material mapping) — reported per quarter. Since SD lead converters are scaled by 4 for correct integration at dt=0.25, KPI extraction divides by 4 to present per-quarter units.
  - Other Clients (by material)
  - Order Basket and Order Delivery (by material)

## Scenario Configuration Schema

One file per run. YAML example below; JSON equivalent is supported.

```yaml
name: "baseline"

runspecs:
  starttime: 2025.0
  stoptime: 2032.0
  dt: 0.25

overrides:
  constants:
    # Anchor Client Parameters (per sector)
    anchor_start_year_Defense: 2025.0
    anchor_client_activation_delay_Defense: 1.0
    anchor_lead_generation_rate_Defense: 0.25
    lead_to_pc_conversion_rate_Defense: 0.75
    project_generation_rate_Defense: 0.5
    max_projects_per_pc_Defense: 2.0
    project_duration_Defense: 4.0
    projects_to_client_conversion_Defense: 3.0
    initial_phase_duration_Defense: 2.0
    ramp_phase_duration_Defense: 8.0
    initial_requirement_rate_Defense: 0.5
    initial_req_growth_Defense: 0.05
    ramp_requirement_rate_Defense: 5.0
    ramp_req_growth_Defense: 0.15
    steady_requirement_rate_Defense: 30.0
    steady_req_growth_Defense: 0.02
    requirement_to_order_lag_Defense: 4.0
    ATAM_Defense: 3.0
    
    # Other Client Parameters (per material)
    lead_start_year_Silicon_Carbide_Fiber: 2025.0
    inbound_lead_generation_rate_Silicon_Carbide_Fiber: 0.5
    outbound_lead_generation_rate_Silicon_Carbide_Fiber: 1.0
    lead_to_c_conversion_rate_Silicon_Carbide_Fiber: 0.75
    lead_to_requirement_delay_Silicon_Carbide_Fiber: 1.0
    requirement_to_fulfilment_delay_Silicon_Carbide_Fiber: 1.0
    avg_order_quantity_initial_Silicon_Carbide_Fiber: 10.0
    client_requirement_growth_Silicon_Carbide_Fiber: 0.05
    TAM_material_Silicon_Carbide_Fiber: 50.0
    
  points:
    # Time-varying lookups (price and capacity per material)
    price_Silicon_Carbide_Fiber:
      - [2025.0, 8000.0]
      - [2026.0, 8000.0]
      - [2027.0, 7500.0]
    max_capacity_Silicon_Carbide_Fiber:
      - [2025.0, 3.0]
      - [2026.0, 3.68]
      - [2027.0, 5.53]
```

### SM-mode additions (Phase 17)

Runspecs:

```yaml
runspecs:
  anchor_mode: sm  # strict per-(sector, material) mode
```

Seeding in SM-mode:

```yaml
seeds:
  active_anchor_clients_sm:
    Defense:
      Silicon Carbide Fiber: 1
```

Examples provided:
- `scenarios/sm_minimal.yaml`: minimal seed-only SM run
- `scenarios/sm_full_demo.yaml`: shows per-(s,m) constant overrides and multi-pair seeds

### Phase 13 — primary_map overrides (multi‑material anchors)

Scenarios can override the sector→materials mapping using `overrides.primary_map`.
This replaces the mapping for the listed sectors and leaves others unchanged.

Schema:

```yaml
overrides:
  primary_map:
    <sector>:
      - { material: <string>, start_year: <float> }
      - ...
```

Rules:
- Sectors and materials must exist in `inputs.json` lists; materials must also exist in `other_params`, `production`, and `pricing`.
- `start_year` must be numeric.
- For each sector listed, the mapping is replaced atomically by the provided list (no partial merges).

Example:

```yaml
name: pm_override_example
runspecs:
  starttime: 2025.0
  stoptime: 2032.0
  dt: 0.25
overrides:
  primary_map:
    Defense:
      - { material: "Silicon Nitride Fiber", start_year: 2026 }
      - { material: "Silicon Carbide Fiber", start_year: 2025 }
    Aviation:
      - { material: "UHT", start_year: 2026 }
      - { material: "Boron_fiber", start_year: 2026 }
```

**Parameter Categories:**

1. **Anchor Client Parameters (per sector)**: All parameters from `Anchor Client Parameters.csv`
   - Timing: `anchor_start_year`, `anchor_client_activation_delay`
   - Lead generation: `anchor_lead_generation_rate`, `lead_to_pc_conversion_rate`
   - Project lifecycle: `project_generation_rate`, `max_projects_per_pc`, `project_duration`, `projects_to_client_conversion`
   - Requirement phases: `initial_phase_duration`, `ramp_phase_duration`, `initial_requirement_rate`, `initial_req_growth`, `ramp_requirement_rate`, `ramp_req_growth`, `steady_requirement_rate`, `steady_req_growth`
   - Order processing: `requirement_to_order_lag`
   - Market limits: `ATAM`

2. **Other Client Parameters (per material)**: All parameters from `Other Client Parameters.csv`
   - Timing: `lead_start_year`
   - Lead generation: `inbound_lead_generation_rate`, `outbound_lead_generation_rate`
   - Conversion: `lead_to_c_conversion_rate`
   - Delays: `lead_to_requirement_delay`, `requirement_to_fulfilment_delay`
   - Order behavior: `avg_order_quantity_initial`, `client_requirement_growth`
   - Market limits: `TAM` (note: the current dataset uses `TAM`, not `TAM_material`)

3. **Time-varying Lookups (per material)**: From `inputs.json` sections `pricing` and `production`
   - `price_<material>`: Price evolution over time (JSON points parsed to lookup)
   - `max_capacity_<material>`: Capacity evolution over time (JSON points parsed to lookup)

**Naming Convention:**
- Constants: `parameter_name_sector` or `parameter_name_material` (using underscores for spaces)
- Points: `price_material` or `max_capacity_material` (using underscores for spaces). Capacity points are per-year; the model scales to per-quarter internally.

**Validation Rules:**
- Keys must match final element names created by the model. Unknown keys are strict errors (no partial application) with nearest-name suggestions.
- Points arrays must be strictly numeric and sorted by time; runner will sort if unsorted.
- Units: years for time, quarters for delays/durations (no dt scaling). Prices/capacity numeric only (currency symbols stripped in CSV loader).
- Percentage values (e.g., `5%`) are converted to decimals (e.g., `0.05`) automatically by the CSV loader.

### Phase 14 — Seeded Starting Inputs (pre‑existing anchors at t0)

Scenarios may seed ACTIVE anchor clients at t0 per sector using a `seeds` block.

Schema:

```yaml
seeds:
  active_anchor_clients:
    <sector>: <int>
    # ...
  # optional aging semantics; if provided, the seeded agents behave as if active for q quarters at step 0
  elapsed_quarters:
    <sector>: <int>
```

Rules and behavior:
- Sectors must exist in `inputs.json` lists; counts must be non‑negative integers.
- Seeded agents are instantiated as ACTIVE before the first step and generate requirements immediately, while respecting sector–material start years.
- ATAM caps leads, so to include seeds in the lead cap without changing equations, the SD stocks are initialized conservatively: `CPC_<sector> = seeds`, and `Cumulative_Agents_Created_<sector> = seeds` for monitoring. Gating remains `If(CPC_<s> < ATAM_<s>, 1, 0)`.

Direct clients seeding:
- Scenarios may also seed direct clients per material under `seeds.direct_clients: { <material>: <int> }`.
- Runner initializes `C_<material>` to the seeded count and clears `Potential_Clients_<material>` to 0. This ensures discrete conversion integrity while enabling seeded demand from direct clients immediately.

## Stepwise Simulation Lifecycle
1. **Initialize**: Read scenario file; create `GrowthGrowthSystem` with `runspecs`.
2. **Load & Validate Data**: Load CSVs; build mappings and check coverage.
3. **Build SD Model**: Create constants, lookups, lead-gen, discrete conversions, delays, capacity, deliveries, revenue.
4. **Create Gateways**: For each material, create `Agent_Demand_Input_<material>` and wire `Total_Demand_<material>` to include it.
5. **Register Factories**: For each sector, register `AnchorClientAgent_<sector>`.
6. **Apply Scenario Overrides**: Set `constant.equation` values and replace `model.points[name]` where provided.
7. **Run Step Loop (t from start to stop at dt)**:
   - Evaluate per-sector agent creation signal. Preferred signal: the integer outflow based on accumulator (e.g., `Agents_To_Create_<sector>` or `Agent_Creation_Outflow_<sector>`).
   - Instantiate that many agents via the sector factory for the current step.
   - Execute `act(...)` for all agents, allowing them to update per-material requirements.
   - Aggregate per-material agent requirements: `sum(requirements[material])` across agents.
   - Update gateway converter numeric equations: `Agent_Demand_Input_<material> = aggregated_value`.
   - **CRITICAL**: Capture KPI values immediately while gateway values are correct for this step.
   - Advance SD one step using the model's scheduler; collect current-period outputs.

Implementation notes:
- SD equations are static; gateway values are numeric and updated per step.
- Prefer the integer outflow (accumulator "fire") to avoid fractional over-creation.
- Maintain deterministic order: instantiate → act → aggregate → set gateways → capture KPIs → advance.

### Gateway Corruption Issue & Fix

**Problem**: During the stepwise run, gateway converters (`Agent_Demand_Sector_Input_<s>_<m>`) are mutated each step to hold numeric constants representing agent demand. After the run completes, these converters retain the final step's values. Post-run KPI extraction evaluating `Total_Demand_<m>` at early times would return final values instead of the correct historical values, causing:
- Early-period Order Basket showing demand that shouldn't exist yet
- Premature material deliveries for inactive sectors/materials  
- Corrupted revenue calculations based on incorrect demand flows

**Solution**: Real-time KPI capture during the stepwise loop. The runner now captures KPI values immediately after updating gateway values and before advancing the model. These historical values are stored and used by the KPI extractor instead of post-run model evaluation, ensuring accurate time-series data that reflects actual simulation dynamics.

**Impact**: Resolves three critical issues:
1. Correct early-period demand values (Order Basket shows 0.0 when expected)
2. Proper material delivery timing (no premature deliveries for inactive materials)
3. Accurate Active Projects KPI (fixed by reordering agent project completion logic)

## KPI Extraction & Outputs (Phase 15)
- Extract per-step series for:
  - **Revenue**: Total, by sector (market), and by material (sum of anchor + direct where applicable).
  - **Anchor Leads**: total + per sector (`CPC_<sector>` as appropriate). In SM-mode the runner computes per-sector leads by summing `Anchor_Lead_Generation_<s>_<m>` converters when `Anchor_Lead_Generation_<s>` is not built.
  - **Active Projects**: computed aggregator (from sector triggers × projects-per-agent proxy) or enhanced to count agent states if desired.
  - **Anchor Clients**: total + per sector (from active-agent proxy or agent counts if enabled in-loop).
  - **Other Leads/Clients**: Other Leads total only (material-driven aggregation); per-sector Other Leads rows are not emitted. Other Clients remain per material.
  - **Order Basket/Delivery**: per material using `Total_Demand` and delivery flows.
- Output: CSV named `Growth_System_Complete_Results.csv`, columns `[Output Stocks, labels...]` where labels are derived from the runspecs grid.
 - Phase 17.6 (optional granularity): When run with flags `--kpi-sm-revenue-rows` and/or `--kpi-sm-client-rows`, the runner appends diagnostic rows `Revenue <sector> <material>` and/or `Anchor Clients <sector> <material>` to the CSV. Defaults leave the CSV surface unchanged.
- ABM metrics requirement (no fallback): The KPI extractor (`extract_and_write_kpis`) requires a per-step ABM metrics list (`agent_metrics_by_step`) with at least as many entries as emitted steps (typically 28). Each entry must include: `t` (float), `active_by_sector` (dict[str,int]), `inprogress_by_sector` (dict[str,int]), `active_total` (int), `inprogress_total` (int). If you do not track ABM state externally, supply a zero-initialized list to emit agent-based KPI rows as zeros. The lower-level collector `collect_kpis_for_step` mandates `step_idx` and `agent_metrics_by_step` and will raise if metrics are missing or out-of-range.

## Logging, Validation, and UI Runner
- **Scenario echo**: dump applied overrides (constants/points) and flag unknown keys.
- **Gateway checks**: per step, sample-log first N steps of `Agent_Demand_Input_<material>` values and totals.
- **Creation checks**: per step, log `Agents_To_Create_<sector>`, created count, cumulative.
- **Capacity & revenue sanity**: log utilization snapshots and period revenue sums; confirm `Total_Revenue ≈ Anchor + Client`.
- **Extraction safeguards**: missing columns default to zeros with warnings; include summary of non-found elements.
  - **UI runner**: Streamlit sidebar supports `--preset` runs and "Validate, Save, and Run" (validate → write YAML with auto‑suffix → run). Logs are tailed from `logs/run.log` during execution and the latest KPI CSV is previewed in-app. When plots (`--visualize`) are generated, the UI renders all PNGs from `output/plots/` with per‑file download buttons. Packaging provides `make` targets and an optional Dockerfile for the UI layer.

## Testing Strategy
- Unit: name creation, scenario parsing, constant/lookup application, gateway update function, per-agent phase logic.
- Integration: single-step and multi-step runs with known small scenarios; compare to hand calculations.
- Regression: pinned scenarios with expected KPIs; CI checks for drift.
  - Additional: short-horizon runner smoke, scheduler integration (two-step with gateway updates), simple sensitivity tests (e.g., price override), and delay-behavior sanity checks. Phase 4 complete: direct-client SD block and JSON lookups integrated; scenario overrides applied strictly by name.

## Performance & Ops
- Stepwise loop adds overhead vs. batch SD; mitigate with:
  - Minimal per-step logging in normal mode; verbose in debug.
  - Vectorize aggregation over agents where possible.
  - Keep dt at 0.25 unless finer resolution is needed.
- Outputs and logs go to `output/` and `logs/`; scenario files in `scenarios/`. Phase 12 saves plots under `output/plots/` when invoked with `--visualize`.

## CLI & Directory Layout
Suggested layout:

```
Growth_growth_system_v2/
  scenarios/
  logs/
  output/
  ui/
  simulate_growth.py        # stepwise runner
  growth_model.py           # SD+ABM model
  technical_architecture.md
  make_lint.py
  requirements.txt
```

## Future Extensions
- Multi-scenario orchestration (external configs, sequential runs, combined comparative CSVs).
- Stochastic per-agent variability (durations, growth) with multiple seeds.
- Visualization (plots of capacity utilization, revenues, client counts).

## UI Helper APIs (Phase 1 for UX)

To support the Streamlit UI without changing core behavior, the following helper
APIs are provided in `src/scenario_loader.py`:

- `list_permissible_override_keys(bundle, anchor_mode="sector"|"sm", extra_sm_pairs=None)`
  Returns sets of permissible override keys derived from the current inputs and
  optional extra (sector, material) pairs. This ensures the UI only exposes
  valid, model-backed names.

- `validate_scenario_dict(bundle, scenario_dict)`
  Validates an in-memory scenario dict (no disk IO) and returns the same
  `Scenario` object as the file-based loader, enabling UI validation before save.

- `summarize_lists(bundle)`
  Returns market/sector/material lists and the sector→materials mapping for UI
  dropdowns and context.

These helpers surface existing validation/naming logic to the UI and do not
modify model or runner behavior.

### Per-(sector, material) parameters by mode (quick reference)

Compact reference of which per-(s,m) anchor parameters are exposed in the UI depending on the run mode. In all cases, defaults can be provided in `inputs.json → anchor_params_sm`, and scenarios may override via `overrides.constants` using canonical names from `anchor_constant_sm(param, sector, material)`.

| Parameter (per‑(s,m)) | Sector mode (anchor_mode = "sector") | SM mode (anchor_mode = "sm") | Notes |
| --- | --- | --- | --- |
| initial_requirement_rate | Visible per‑(s,m) | Visible per‑(s,m) | Requirement family allowed in both modes |
| initial_req_growth | Visible per‑(s,m) | Visible per‑(s,m) |  |
| ramp_requirement_rate | Visible per‑(s,m) | Visible per‑(s,m) |  |
| ramp_req_growth | Visible per‑(s,m) | Visible per‑(s,m) |  |
| steady_requirement_rate | Visible per‑(s,m) | Visible per‑(s,m) |  |
| steady_req_growth | Visible per‑(s,m) | Visible per‑(s,m) |  |
| requirement_to_order_lag | Visible per‑(s,m) | Visible per‑(s,m) | Sector‑mode falls back to sector‑level if per‑(s,m) absent |
| anchor_start_year | Not per‑(s,m) (sector‑level only) | Visible per‑(s,m) | Full per‑(s,m) set only in SM mode |
| anchor_client_activation_delay | Not per‑(s,m) | Visible per‑(s,m) |  |
| anchor_lead_generation_rate | Not per‑(s,m) | Visible per‑(s,m) |  |
| lead_to_pc_conversion_rate | Not per‑(s,m) | Visible per‑(s,m) |  |
| project_generation_rate | Not per‑(s,m) | Visible per‑(s,m) |  |
| max_projects_per_pc | Not per‑(s,m) | Visible per‑(s,m) |  |
| project_duration | Not per‑(s,m) | Visible per‑(s,m) |  |
| projects_to_client_conversion | Not per‑(s,m) | Visible per‑(s,m) |  |
| initial_phase_duration | Not per‑(s,m) | Visible per‑(s,m) |  |
| ramp_phase_duration | Not per‑(s,m) | Visible per‑(s,m) |  |
| ATAM | Not per‑(s,m) | Visible per‑(s,m) |  |

UI note: After applying proposed sector→material mappings in the Primary Map editor, the Constants tab expands its permissible list to include those pairs. Sector mode shows only the requirement_* family per‑(s,m); SM mode exposes the full per‑(s,m) anchor set above.

## Notes & Conventions
- Numeric units: all delays and durations are in quarters; no dt scaling needed.
- CSV cleaning: strip currency/percent signs, convert to numeric, guard NaNs.
- Naming: consistent `create_element_name` usage for all elements referenced in scenarios.

---
This document specifies a clean, BPTK_Py-aligned architecture to start fresh, enabling precise scenario planning with a simple, deterministic hybrid coupling (Pattern 1) and externalized scenario inputs.

## Cross-reference to System Logic (spec_sheet.txt)

The following maps the business/system logic to this architecture:

- Anchor lead generation (per sector): Implemented with `Anchor_Lead_Generation_<s>`, `CPC_<s>`, and gating on `ATAM_<s>` and `anchor_start_year_<s>`.
- Potential Clients (PC) and conversion to AC: The spec’s SD project-conversion structure (PC stock, project starts/completions, threshold to AC) is realized via ABM lifecycle on `AnchorClientAgent` (projects started and completed per agent, activation threshold, activation delay). This preserves the intended behavior while moving it from SD to agents.
- Requirement generation per AC (per primary material): Implemented inside agents with initial/ramp/steady phases and sector parameters, mapped 1:1 to the spec.
- Requirement→Order lag per sector and material: Supported by computing per-sector, per-material orders with `Material_Orders_<s>_<m> = delay(model, Agent_Demand_<s>_<m>, requirement_to_order_lag_<s>_<m>)`. If `<s>_<m>` is not provided in inputs, the model uses the sector-level `requirement_to_order_lag_<s>` as a fallback (Phase 16 precedence).
- Capacity-capped fulfillment: Implemented as `Anchor_Delivery_Flow_<m> = min(sum_s Material_Orders_<s>_<m>, max_capacity_lookup_<m>)` and `Client_Fulfilment` as per spec (see equations below). This matches the spec’s MIN-at-fulfillment logic.
- General lead-gen & direct client orders: Implemented as SD per material with discrete client conversion, order delays, fulfillment delay, and capacity limits. Number of leads is capped by TAM{material}
- Revenue: Calculated from delivery flows × price lookups (quarterly), matching the spec’s directive to use flows (not cumulative stocks) for revenue.
- Optional cumulative stocks for delivered orders/revenue: Supported as optional stocks; not required for the KPI flows but available if needed.


## Explicit Equations & Element Names

This section lists the canonical equations and the exact element names to be created by the model so that scenarios can reliably override them and the runner can read/write them.

- Anchor lead generation per sector s:
  - `Anchor_Lead_Generation_<s> = anchor_lead_generation_rate_<s> * If(time >= anchor_start_year_<s>, 1, 0) * If(CPC_<s> < ATAM_<s>, 1, 0)`
  - `CPC_<s>` is a stock with `equation = Anchor_Lead_Generation_<s>` and `initial_value = 0`.
  - `New_PC_Flow_<s> = Anchor_Lead_Generation_<s> * lead_to_pc_conversion_rate_<s>`

- Fractional agent creation per sector s (accumulate-and-fire):
  - Stock: `Agent_Creation_Accumulator_<s>` with `equation = Agent_Creation_Inflow_<s> - Agent_Creation_Outflow_<s>`, `initial_value = 0`.
  - Inflow: `Agent_Creation_Inflow_<s> = New_PC_Flow_<s>`
  - Outflow: `Agent_Creation_Outflow_<s> = max(0, round(Agent_Creation_Accumulator_<s> - 0.5, 0))`
  - Converter (integer agents to create this step): `Agents_To_Create_<s> = max(0, round(Agent_Creation_Accumulator_<s> - 0.5, 0))`
  - Cumulative created (stock): `Cumulative_Agents_Created_<s>` with inflow `Cumulative_Inflow_<s> = Agent_Creation_Outflow_<s>`
  - Legacy trigger (monitoring): `Agent_Creation_Trigger_<s> = New_PC_Flow_<s>`

 - Direct clients per material m (discrete conversion):
  - `Inbound_Leads_<m> = inbound_lead_generation_rate_<m> * If(time >= lead_start_year_<m>, 1, 0) * If(CL_<m> < TAM_<m>, 1, 0)`
  - `Outbound_Leads_<m>` analogous; `CL_<m>` accumulates inbound + outbound.
  - `Total_New_Leads_<m> = Inbound_Leads_<m> + Outbound_Leads_<m>`
  - `Fractional_Client_Conversion_<m> = Total_New_Leads_<m> * lead_to_c_conversion_rate_<m>`
  - `Potential_Clients_<m>` stock accumulates fractional conversions minus `Client_Creation_<m>`
  - `Client_Creation_<m> = max(0, round(Potential_Clients_<m> - 0.5, 0))`
  - `C_<m>` accumulates `Client_Creation_<m>`
  - `avg_order_quantity_<m> = avg_order_quantity_initial_<m> * (1 + client_requirement_growth_<m>)^(max(0, time - lead_start_year_<m>))`
  - `Client_Requirement_<m> = delay(model, C_<m> * avg_order_quantity_<m>, lead_to_requirement_delay_<m>)`

- Capacity & lookups per material m:
  - `max_capacity_lookup_<m> = lookup(time, max_capacity_<m>)`
  - `Price_<m> = lookup(time, price_<m>)`

- ABM→SD gateway per sector–material (s,m):
  - `Agent_Demand_Sector_Input_<s>_<m>` is a converter with a numeric equation updated per step by the runner (no dependencies).
  - `Agent_Aggregated_Demand_<m> = sum_over_sectors_s(Agent_Demand_Sector_Input_<s>_<m>)`
  - `Total_Demand_<m> = Agent_Aggregated_Demand_<m> + Client_Requirement_<m>`
  - `Fulfillment_Ratio_<m> = min(1, If(Total_Demand_<m> > 0, max_capacity_lookup_<m> / Total_Demand_<m>, 1))`

 - Deliveries:
  - Anchor (per sector with sector–material lag L_{s,m}): For each sector s that uses m,
    - `Delayed_Agent_Demand_<s>_<m> = Agent_Demand_Sector_Input_<s>_<m> * Fulfillment_Ratio_<m>`
    - `Anchor_Delivery_Flow_<s>_<m> = delay(model, Delayed_Agent_Demand_<s>_<m>, requirement_to_order_lag_<s>_<m>)`
    - `Anchor_Delivery_Flow_<m> = sum_over_sectors_s( Anchor_Delivery_Flow_<s>_<m> )`
  - Client delivery: `Client_Delivery_Flow_<m> = delay(model, Delayed_Client_Demand_<m>, requirement_to_fulfilment_delay_<m>)`
    - `Delayed_Client_Demand_<m> = Client_Requirement_<m> * Fulfillment_Ratio_<m>`

- Revenue:
  - Sector-level anchor revenue: `Anchor_Revenue_<s>_<m> = Anchor_Delivery_Flow_<s>_<m> * Price_<m>` and `Anchor_Revenue_<s> = sum_m(Anchor_Revenue_<s>_<m>)`
  - Material-level revenues: `Anchor_Revenue_<m> = sum_s(Anchor_Revenue_<s>_<m>)`; `Client_Revenue_<m> = Client_Delivery_Flow_<m> * Price_<m>`
  - Totals: `Anchor_Revenue = sum_m(Anchor_Revenue_<m>)`; `Client_Revenue = sum_m(Client_Revenue_<m>)`; `Total_Revenue = Anchor_Revenue + Client_Revenue`

All element names use underscores for spaces and the `<suffix>` convention above.

## Scenario Schema (Detailed)

Informal schema (YAML shown; JSON equivalent allowed):

```yaml
name: <string>                # scenario label
runspecs:                     # optional (defaults: 2025.0→2032.0, dt=0.25)
  starttime: <float>
  stoptime: <float>
  dt: <float>

overrides:                    # optional blocks
  constants:                  # map of element_name → numeric value
    <element_name>: <float>
  points:                     # map of lookup_name → list[[time, value], ...]
    <lookup_name>:
      - [<float_time>, <float_value>]
      - ...
```

Validation rules:
- Keys must match final element names created by the model. Runner logs unknown keys and nearest matches.
- Points arrays must be strictly numeric and sorted by time; runner will sort if unsorted.
- Units: years for time, quarters for delays/durations (no dt scaling). Prices/capacity numeric only (currency symbols stripped in CSV loader).

Sample JSON:

```json
{
  "name": "brave-puppy",
  "runspecs": { "starttime": 2025.0, "stoptime": 2032.0, "dt": 0.25 },
  "overrides": {
    "constants": {
      "anchor_lead_generation_rate_Defense": 1.3,
      "lead_to_pc_conversion_rate_Defense": 0.7
    },
    "points": {
      "max_capacity_Silicon_Carbide_Fiber": [[2025.0, 10000.0],[2026.0, 12000.0]],
      "price_Silicon_Carbide_Fiber": [[2025.0, 350.0],[2026.0, 340.0]]
    }
  }
}
```

## Runner Pseudocode (Stepwise)

```text
load scenario (yaml/json)
sys = GrowthGrowthSystem(starttime, stoptime, dt)
sys.load_and_validate_data()
sys.build_model()
sys.add_gateway_converters_for_all_materials()
sys.register_anchor_agent_factories()
apply_overrides(sys, scenario.overrides)

state = initialize_output_state()
for each time step t from start to stop (inclusive of first, exclusive of last):
  # read integer creation signals
  for each sector s:
    k = value_of(sys, "Agents_To_Create_<s>", at t)
    create k agents via factory "AnchorClientAgent_<s>"

  # agent actions
  for each agent a:
    a.act(t, round, step)

  # aggregate agent demand by material m
  for each material m:
    agg[m] = sum(a.requirements[m] for all agents)
    set_equation(sys, "Agent_Demand_Input_<m>", agg[m])

  # advance SD one step and collect outputs for time index t
  advance_one_step(sys)
  capture_outputs_into(state)

write_csv(state)
```

Notes:
- “value_of” uses the model’s current step values for converters/stocks/flows.
- “advance_one_step” uses the model’s scheduler rather than a full-batch runner.

## KPI Mapping (Elements → Output Rows)
- Revenue total: `Total_Revenue` → row: `Revenue`
- Revenue by sector s: `Anchor_Revenue_<s>` (sum over materials of sector anchor revenue only) → row: `Revenue <s>`
- Revenue by material m: `Anchor_Revenue_<m> + Client_Revenue_<m>` → row: `Revenue <m>`
- Anchor Leads total: sum of `CPC_<s>` changes per quarter → row: `Anchor Leads`
- Anchor Leads by sector s: `CPC_<s>` → row: `Anchor Leads <s>`
- Active Projects total: proxy or agent-state count; default proxy = sum over s `(Agent_Creation_Trigger_<s> * max_projects_per_pc_<s>)` → row: `Active Projects`
- Active Projects by sector s: zero rows (as per expected format) or extend later.
- Anchor Clients total: `Total_Active_Anchor_Clients` (proxy or agent-state count) → row: `Anchor Clients`
- Anchor Clients by sector s: `Active_Anchor_Clients_<s>` → row: `Anchor Clients <s>`
- Other Leads total: sum over materials of `CL_<m>` increments, reported per quarter (divide SD evaluation by 4) → row: `Other Leads`
  
- Other Clients by material m: `C_<m>` → row: `Other Clients <m>`
- Order Basket by material m: `Total_Demand_<m>` → row: `Order Basket <m>`
- Order Delivery by material m: `Anchor_Delivery_Flow_<m> + Client_Delivery_Flow_<m>` → row: `Order Delivery <m>`

## Quarter Labeling & Time Grid (Phase 15)
- Time grid: `[starttime + i*dt for i in 0..num_steps-1]` with arbitrary positive `dt`.
- Output periods: one column per simulated step; labels derived from each absolute time by mapping fractional year to nearest quarter (Q1=.00, Q2=.25, Q3=.50, Q4=.75).
- No fixed 28-step padding or truncation.

## Validation & Acceptance Checklist
- Data load: all required sectors/materials present across JSON sections; fail on missing coverage.
- Lists contain `'US'` market (US-only scope in this phase).
- Root contains `'lists'` key.
- Equations: delays use quarters directly (no dt scaling); lookups accept 0 values without NaN.
- Agent creation: per-step `Agents_To_Create_<s>` non-negative integer; accumulator drains via outflow.
- Gateways: non-negative values; logged snapshots for first and mid/last steps.
- Capacity utilization: `Fulfillment_Ratio_<m> ∈ [0,1]`.
- Revenue identity: `Total_Revenue ≈ Anchor_Revenue + Client_Revenue` within numerical tolerance each step.
- Outputs: exact column count (29 including label or 28 data columns), correct row labels, deterministic across runs with same inputs.

## Error Handling & Logging Policy
- Unknown override keys: strict error with nearest-name suggestions (Phase 11 tightening).
- Points data: strict validation in the scenario loader; numeric and strictly increasing times required.
- Missing elements in extraction: gateway-dependent values are captured during the run; fallback returns 0.0 for non-existent elements.
- Lookup tails: hold-last policy; the runner logs WARN if `t` is below the first or above the last defined point for any capacity/price lookup encountered at a step.
- Logging levels: INFO for major milestones, DEBUG for step snapshots; logs to `logs/` and console.

### Futher Guidelines
- Ensure agents created during steps only.
- Confirm all delays are used as-quarter values (no dt multiplication).
- Keep enhanced naming strategy; add collision checks.
- Externalize scenarios; implement override application and validation.
- Use runner with scheduler-driven loop


