## Product Growth System – Technical Architecture (BPTK_Py Hybrid, Pattern 1)

### Purpose
Enable robust scenario planning for revenue and KPIs by aligning the model and runner with BPTK_Py's hybrid SD+ABM capabilities. This architecture treats each Anchor Client as an agent, couples agent behavior to SD via a stepwise ABM→SD gateway, and externalizes scenario inputs in JSON/YAML. Single-scenario execution per run is prioritized for simplicity and reliability.

The system is designed to be industry-agnostic, allowing you to model any sectors and products by configuring the inputs. No hard-coded industry assumptions are made.

### Objectives & Scope
- **Objectives**: Scenario planning with tweakable exogenous/endogenous inputs; quarterly KPIs (revenue, leads, clients, deliveries, baskets, projects).
- **Scope**: Hybrid model (SD core + ABM for Anchor Clients) with stepwise coupling; scenario configs; deterministic CSV outputs; comprehensive logging.
- **Out of scope (initial)**: Multi-scenario batch runs; stochastic effects; interactive plotting. Phase 12 adds static, read-only plotting as post-processing of the CSV and packaging conveniences (Makefile, optional UI container).

## High-Level Design

### UI Architecture (Streamlit Layer)

- Goals: Thin, isolated UI that never mutates the model; use YAML + CLI only.
- Structure under `ui/` (Phase 1 scaffold):
  - `ui/app.py`: Minimal 9-tab Streamlit entrypoint wiring (Simulation Definitions, Simulation Specs, Primary Mapping, Seeds, Client Revenue, Direct Market Revenue, Lookup Points, Runner, Logs).
  - `ui/state.py`: Rich typed state retained for compatibility with backend helpers (simplification planned in later phases).
  - `ui/components/`: New tab components with a `BaseComponent` pattern and per-tab `render_*_tab(state)` entrypoints; placeholders for tabs not yet implemented.
  - `ui/services/`: Rebuilt services (`scenario_service.py`, `validation_service.py`, `execution_service.py (stub)`) replacing legacy builder/runner clients.
- Data flow:
  1) User edits → in-memory scenario dict
  2) Validate via backend `validate_scenario_dict`
  3) Save YAML to `scenarios/` using ScenarioService
  4) (Later phases) Run CLI with Runner service, tail logs, preview results
- Data flow:
  1) Load inputs (`Phase1Bundle`) → get permissible keys and lists
  2) User edits → build in‑memory `scenario_dict`
  3) Validate with `validate_scenario_dict`
  4) Save YAML to `scenarios/`
  5) Run CLI in subprocess → tail logs → preview KPI CSV (optional `--visualize`; UI renders `output/plots/*.png` inline when present)
- Isolation: UI uses only public helpers; runner executed as subprocess; no SD/ABM imports in components.
- Packaging: `Makefile` targets (`install`, `run_ui`, `run_baseline`, `test`, `lint`); optional `Dockerfile.ui` to containerize the UI (mount `scenarios/`, `logs/`, `output/`).

### **NEW UI STRUCTURE (Phases 1–3 Completed)**

The UI has been restructured with a new 9-tab system and Phase 1 scaffold implemented:

**Tab 1: Simulation Definitions** ✅ **COMPLETED**
- Market, sector, and product list management
- Table-based input with add/edit/delete functionality
- Save button protection to prevent accidental changes
- Dynamic content management

**Tab 2: Simulation Specs** ✅ **COMPLETED (Phase 1)**
- Runtime controls (start time, stop time, dt)
- Anchor mode selection (Sector vs Sector+Product mode)
- Explicit scenario management UX:
  - Load existing: dropdown + "Load Selected Scenario"; overwrite current button directly below
  - Save options: "New scenario name" + "Save as New" (guarded against duplicates)

**Tab 3: Primary Mapping** ✅ **COMPLETED**
- Sector-wise product selection
- Mapping insights and summary
- Dynamic table generation

**Tab 4: Client Revenue** ✅ **COMPLETED (Phase 3)**
- Table-based editors with unit/format hints
- Market Activation and Orders groups (19 params total)
- Only shows sector–product pairs selected in Primary Mapping

**Tab 5: Direct Market Revenue** ✅ **COMPLETED (Phase 3)**
- Table-based editors with unit/format hints (9 params)
- Product-specific; Enter-to-commit values

**Tab 6: Lookup Points** ✅ **COMPLETED (Phase 3)**
- Tables for pricing and capacity time series (years as rows, products as columns)
- Enter-to-commit; per-subtab Reset rebuilds tables from last‑saved YAML and rotates editor keys to ensure deterministic redraw. Seeds tab supports Reset to scenario snapshot.

**Tab 7: Runner** 🚧 **PLACEHOLDER (Phase 8)**
- Scenario execution and monitoring
- Save, validate, and run controls

**Tab 8: Logs** 🚧 **PLACEHOLDER (Phase 8)**
- Simulation logs and monitoring
- Log filtering and export functionality

**Legacy Functions**: Successfully integrated into the new 8-tab structure. All functionality now available through the modern tab-based interface.

#### Phase 3 Known Issue
- Reset to default in Client Revenue and Direct Market Revenue tables may not visually restore YAML values in all cases due to Streamlit data_editor widget state retaining edits. Temporary workaround: reload the scenario from the Simulation Specs tab to rehydrate tables from YAML. A follow-up enhancement will make Reset deterministically reflect YAML without requiring a full table rebuild.

### Modeling Approach
- **Hybrid Pattern 1 (recommended)**: Predefine per-product gateway converters that accept numeric inputs each time step. The runner computes aggregated agent demand and sets gateway values before advancing the SD step.
- **Why this pattern**: Minimal intrusion, explicit data flow, easy logging and validation, and fully compatible with BPTK_Py's deterministic SD equation evaluation.

### Core Components
- **System Dynamics (SD) Model**
  - Implements the spec in `spec_sheet.txt`: lead-gen, project conversion, requirement generation, capacity, fulfillment, and revenue.
  - Uses BPTK_Py stocks/flows/converters/lookup tables for time-continuous dynamics at dt = 0.25 (quarterly).

- **Agent-Based Model (ABM)**
  - `AnchorClientAgent` per sector; each agent has lifecycle and generates product-specific requirements according to three phases (initial, ramp, steady), activation delays, and sector-specific parameters.
  - Agents act each time step to update per-product requirements.
  - Phase 17.3 (SM‑mode ABM): `AnchorClientAgentSM` bound to a single (sector, product) with a self‑contained lifecycle (POTENTIAL → PENDING_ACTIVATION → ACTIVE). Factory `build_sm_anchor_agent_factory(sector, product)` constructs agents strictly from `anchor_params_sm` for the pair (no sector fallbacks). Requirements are generated only when ACTIVE and after `anchor_start_year_<s>_<p>`.

- **ABM→SD Gateway Converters (per sector–product)**
  - For each sector s and product p used by s, define a converter `Agent_Demand_Sector_Input_<s>_<p>` with a numeric equation (value set by runner each step).
  - Define `Agent_Aggregated_Demand_<p> = sum_over_sectors_s(Agent_Demand_Sector_Input_<s>_<p>)`.
  - `Total_Demand_<p> = Agent_Aggregated_Demand_<p> + Client_Requirement_<p>`
  - Capacity, deliveries, and revenue use `Total_Demand_<p>` while retaining sector attribution for anchor deliveries. Sectors may map to multiple products; the model constructs `Agent_Demand_Sector_Input_<s>_<p>` and `Anchor_Delivery_Flow_<s>_<p>` for every mapped pair and aggregates by product and by sector for KPIs.

- **Scenario Configuration (JSON/YAML)**
  - One scenario file per run; provides constants and lookup overrides using exact model element names.
  - Runner supports `--preset <name>` to select files under `scenarios/`. Unknown override keys are strict errors with nearest-name suggestions; overrides are validated against built model elements before application (no partials). In SM‑mode (17.5 strictness), only per‑(s,p) anchor constants are permissible override keys for anchor parameters.
  - UI (Phases 3–11) builds an in‑memory scenario via tabs for runspecs, constants, points, primary map, and seeds; validates using `src.scenario_loader.validate_scenario_dict`; can write YAML to `scenarios/`; can load/duplicate scenarios; supports deterministic Reset from last‑saved YAML per subtab; and can run either a named preset or the current scenario from the sidebar. The UI does not alter model logic; it is an isolated layer under `ui/`.
  - Phase 2 UI save semantics: On save, the UI writes a complete `overrides.primary_map` snapshot matching the Primary Mapping tab for all sectors (empty lists mean “no mapping”). In SM mode, the UI also auto‑derives and writes `lists_sm` from the current mapping so the per‑(sector, product) universe is consistent with the UI selection.
- **PLANNED UI RESTRUCTURING**: The UI will be restructured to use table-based input for improved user experience while maintaining the same backend integration and YAML compatibility. New tabs will include Simulation Definitions, Client Revenue, and Direct Market Revenue, with save button protection to prevent accidental parameter changes.
  - After a run, the runner writes the default CSV and an additional copy for comparisons. When invoked with `--output-name <name>`, it also writes a timestamped CSV `<name>_YYMMDDHHMMSS.csv` in `output/`. This does not change KPI logic or model state.

- **Stepwise Simulation Runner**
  - Initializes model, registers agent factories, builds SD structure, creates gateways, applies scenario overrides.
  - Executes a per-step loop: reads SD triggers, creates agents, runs agent actions, aggregates per-product demand, sets gateway converter values, advances SD one step using the scheduler (`run_step`), collects outputs.
  - SM-mode (Phase 17.4/17.5): per-(sector, product) creation signals `Agents_To_Create_<s>_<p>` drive instantiation via SP factories; SP seeding initializes `CPC_<s>_<p>` and `Cumulative_Agents_Created_<s>_<p>`; KPI capture sums `Anchor_Lead_Generation_<s>_<p>` when sector-level is absent. Strict rules: sector-level creation and seeding are disallowed in SM-mode; `lists_sm` must be explicit in `inputs.json`; full `anchor_params_sm` coverage is required for every pair, including all 20 anchor parameters (timing, lifecycle, phase durations/rates/growths, ATAM, requirement-to-order lag, and requirement_limit_multiplier).

## Data Inputs
- JSON-first (`inputs.json`) with strict validation:
  - Top-level `'lists'` is required; lists are reconstructed US-only in this phase and must include `'US'`.
  - `anchor_params` (per sector), `other_params` (per product), `production` (per product by year), `pricing` (per product by year), `primary_map` (sector→products with start_year). Phase 16 adds optional `anchor_params_sm` (per-(sector, product) targeted parameters) and optional `lists_sm` (explicit SP universe; if absent, derived from `primary_map`).
  - Primary map entries with `start_year <= 0` are allowed but logged as warnings (treated as disabled).
  - Production/Pricing time series must have strictly increasing years and non-negative values.
  - SM‑mode (Phase 17.5): requires explicit `lists_sm` (not derived) and complete `anchor_params_sm` coverage for the full anchor set per pair listed in the implementation plan.

## Naming & Dimensions
- Use `create_element_name(base[, sector][, product])` to generate BPTK-compatible names: underscores for spaces, generous length limit (~100 chars) with hash-based truncation only if needed; detect collisions. Phase 16 adds `anchor_constant_sm(param, sector, product)` for per-(s,p) constants names (e.g., `requirement_to_order_lag_Defense_Silicon_Carbide_Fiber`).
- Names should remain stable across runs so scenarios can reliably override elements.

## SD Structure (essential elements)
- Anchor lead-gen per sector: `Anchor_Lead_Generation_<sector>`, `CPC_<sector>`, `New_PC_Flow_<sector>`.
- Project conversion per sector using "accumulate-and-fire" logic; activation delays drive AC activation.
- **NEW: Direct client cohort submodel per product**: leads → discrete clients → cohort aging chain → requirements (with delays) → fulfillment.
  - Cohort aging chain: `Direct_Client_Cohort_0_<product>`, `Direct_Client_Cohort_1_<product>`, ... (one bucket per simulated quarter)
  - Per-cohort order calculation: `min(base_order + linear_growth × age, base_order × cap_multiplier)`
  - Total orders: `Cohort_Effective_Orders_<product> = sum_over_ages(cohort_size × per_client_order_at_age)`
- Capacity per product via `max_capacity_lookup_<product>` converter (lookup on `max_capacity_<product>(Time)`).
- Total demand per product: `Total_Demand_<product> = Agent_Demand_Input_<product> + Client_Requirement_<product>`.
- Fulfillment ratio, delivery flows:
  - `Anchor_Delivery_Flow_<product>` (delayed, capacity-constrained sum of sector agent demands).
  - `Client_Delivery_Flow_<product>` (delayed, capacity-constrained client fulfillment).
- Revenue: `Price_<product> = lookup(price_<product>, Time)`, then `Anchor_Revenue`, `Client_Revenue`, `Total_Revenue`.

## ABM Structure (essential elements)
- `AnchorClientAgent` properties: sector, parameters, `primary_products`, `state`, per-product `requirements`, `activation_time`, project counters.
- `act(time, round_no, step_no)`: complete due projects, start projects if eligible, switch to ACTIVE when threshold met, generate requirements by phase for relevant products.
- Per-step outputs used by runner to aggregate requirements by product.
- Phase 17.3: `AnchorClientAgentSM` properties: sector, product, strict per‑(s,p) params, lifecycle state, activation time, project counters; `act(...)` updates a single-product requirement per step with initial/ramp/steady phases.

## System Logic Overview (plain language)

This captures the business intent without technical details:

- Structure
  - Markets contain sectors; each sector uses one or more primary products starting in specific years.
  - Two channels: Anchor clients (sector-specific, agent-based) and Other clients (product-specific, aggregated SD).

- Anchor clients (per sector, per client)
  - Leads are generated at a sector rate, capped by an addressable limit (ATAM). Leads accumulate to Potential Clients (PC).
  - PCs start projects up to a max projects-per-PC; projects complete after a duration.
  - When completed projects reach a threshold, the PC becomes an Active Client after an activation delay.
  - Active clients generate requirements for the sector's primary products in three phases (initial, ramp, steady) with configurable rates/growth and product start years. Requirement growth can be limited via `requirement_limit_multiplier` to prevent unlimited growth.
- **NEW Phase Transition Behavior**: By default, each phase inherits the ending value from the previous phase. Override parameters allow explicit starting values when needed.

- Other (direct) clients (per product)
  - Inbound and outbound leads accrue, capped by a product TAM.
  - Discrete client creation uses accumulate-and-fire (only whole clients are created).
  - **NEW: Cohort-based order system**: Clients are organized into cohorts by creation quarter. Each cohort starts with base order quantity and grows linearly over time, with per-client order limits. Total orders = sum across all cohorts of (cohort_size × per-client_order_at_age). Requirements convert to orders via a lead-to-requirement delay and are fulfilled after a fulfillment delay.

- Demand aggregation and fulfillment
  - Total demand per product = Anchor agent demand (sum across sectors) + Direct client requirements.
  - Each product has a time-varying capacity; fulfillment uses a proportional ratio across channels by default.
  - Anchor orders use sector–product specific requirement-to-order lags; direct client orders include fulfillment delays.

- Pricing & Revenue
  - Product prices vary over time.
  - Quarterly revenue = deliveries × price; computed for Anchor and Direct, then summed.

- KPIs (quarterly)
  - Revenue (total, by sector, by product)
  - Anchor Leads, Anchor Clients, Active Projects
  - Other Leads (total and by sector via product mapping) — reported per quarter. Since SD lead converters are scaled by 4 for correct integration at dt=0.25, KPI extraction divides by 4 to present per-quarter units.
  - Other Clients (by product)
  - Order Basket and Order Delivery (by product)

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
    
    # Other Client Parameters (per product)
    lead_start_year_Silicon_Carbide_Fiber: 2025.0
    inbound_lead_generation_rate_Silicon_Carbide_Fiber: 0.5
    outbound_lead_generation_rate_Silicon_Carbide_Fiber: 1.0
    lead_to_c_conversion_rate_Silicon_Carbide_Fiber: 0.75
    lead_to_requirement_delay_Silicon_Carbide_Fiber: 1.0
    requirement_to_fulfilment_delay_Silicon_Carbide_Fiber: 1.0
    avg_order_quantity_initial_Silicon_Carbide_Fiber: 10.0
    client_requirement_growth_Silicon_Carbide_Fiber: 0.05
    TAM_product_Silicon_Carbide_Fiber: 50.0
    
  points:
    # Time-varying lookups (price and capacity per product)
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
  anchor_mode: sm  # strict per-(sector, product) mode
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
- `scenarios/sm_full_demo.yaml`: shows per-(s,p) constant overrides and multi-pair seeds

### Phase 13 — primary_map overrides (multi‑product anchors)

Scenarios can override the sector→products mapping using `overrides.primary_map`.
This replaces the mapping for the listed sectors and leaves others unchanged.

Schema:

```yaml
overrides:
  primary_map:
    <sector>:
      - { product: <string>, start_year: <float> }
      - ...
```

Rules:
- Sectors and products must exist in `inputs.json` lists; products must also exist in `other_params`, `production`, and `pricing`.
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
      - { product: "Silicon Nitride Fiber", start_year: 2026 }
      - { product: "Silicon Carbide Fiber", start_year: 2025 }
    Aviation:
      - { product: "UHT", start_year: 2026 }
      - { product: "Boron_fiber", start_year: 2026 }
```

**Parameter Categories:**

1. **Anchor Client Parameters (per sector)**: All parameters from `Anchor Client Parameters.csv`
   - Timing: `anchor_start_year`, `anchor_client_activation_delay`
   - Lead generation: `anchor_lead_generation_rate`, `lead_to_pc_conversion_rate`
   - Project lifecycle: `project_generation_rate`, `max_projects_per_pc`, `project_duration`, `projects_to_client_conversion`
   - Requirement phases: `initial_phase_duration`, `ramp_phase_duration`, `initial_requirement_rate`, `initial_req_growth`, `ramp_requirement_rate`, `ramp_req_growth`, `steady_requirement_rate`, `steady_req_growth`, `ramp_requirement_rate_override`, `steady_requirement_rate_override`
   - Order processing: `requirement_to_order_lag`
   - Growth limits: `requirement_limit_multiplier` (multiplier of initial rate for hard stop on requirement growth)
   - Market limits: `ATAM`

2. **Other Client Parameters (per product)**: All parameters from `Other Client Parameters.csv`
   - Timing: `lead_start_year`
   - Lead generation: `inbound_lead_generation_rate`, `outbound_lead_generation_rate`
   - Conversion: `lead_to_c_conversion_rate`
   - Delays: `lead_to_requirement_delay`, `requirement_to_fulfilment_delay`
   - Order behavior: `avg_order_quantity_initial`, `client_requirement_growth`
   - **NEW: Cohort system**: `requirement_limit_multiplier` (per-client order cap as multiplier of base)
   - Market limits: `TAM` (note: the current dataset uses `TAM`, not `TAM_product`)

3. **Time-varying Lookups (per product)**: From `inputs.json` sections `pricing` and `production`
   - `price_<product>`: Price evolution over time (JSON points parsed to lookup)
   - `max_capacity_<product>`: Capacity evolution over time (JSON points parsed to lookup)

**Naming Convention:**
- Constants: `parameter_name_sector` or `parameter_name_product` (using underscores for spaces)
- Points: `price_product` or `max_capacity_product` (using underscores for spaces). Capacity points are per-year; the model scales to per-quarter internally.

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
- Seeded agents are instantiated as ACTIVE before the first step and generate requirements immediately, while respecting sector–product start years.
- ATAM caps leads, so to include seeds in the lead cap without changing equations, the SD stocks are initialized conservatively: `CPC_<sector> = seeds`, and `Cumulative_Agents_Created_<sector> = seeds` for monitoring. Gating remains `If(CPC_<s> < ATAM_<s>, 1, 0)`.

Direct clients seeding:
- Scenarios may also seed direct clients per product under `seeds.direct_clients: { <product>: <int> }`.
- Runner initializes `C_<product>` to the seeded count and clears `Potential_Clients_<product>` to 0. This ensures discrete conversion integrity while enabling seeded demand from direct clients immediately.

## Stepwise Simulation Lifecycle
1. **Initialize**: Read scenario file; create `GrowthGrowthSystem` with `runspecs`.
2. **Load & Validate Data**: Load CSVs; build mappings and check coverage.
3. **Build SD Model**: Create constants, lookups, lead-gen, discrete conversions, delays, capacity, deliveries, revenue.
4. **Create Gateways**: For each product, create `Agent_Demand_Input_<product>` and wire `Total_Demand_<product>` to include it.
5. **Register Factories**: For each sector, register `AnchorClientAgent_<sector>`.
6. **Apply Scenario Overrides**: Set `constant.equation` values and replace `model.points[name]` where provided.
7. **Run Step Loop (t from start to stop at dt)**:
   - Evaluate per-sector agent creation signal. Preferred signal: the integer outflow based on accumulator (e.g., `Agents_To_Create_<sector>` or `Agent_Creation_Outflow_<sector>`).
   - Instantiate that many agents via the sector factory for the current step.
   - Execute `act(...)` for all agents, allowing them to update per-product requirements.
   - Aggregate per-product agent requirements: `sum(requirements[product])` across agents.
   - Update gateway converter numeric equations: `Agent_Demand_Input_<product> = aggregated_value`.
   - **CRITICAL**: Capture KPI values immediately while gateway values are correct for this step.
   - Advance SD one step using the model's scheduler; collect current-period outputs.

Implementation notes:
- SD equations are static; gateway values are numeric and updated per step.
- Prefer the integer outflow (accumulator "fire") to avoid fractional over-creation.
- Maintain deterministic order: instantiate → act → aggregate → set gateways → capture KPIs → advance.

### Gateway Corruption Issue & Fix

**Problem**: During the stepwise run, gateway converters (`Agent_Demand_Sector_Input_<s>_<p>`) are mutated each step to hold numeric constants representing agent demand. After the run completes, these converters retain the final step's values. Post-run KPI extraction evaluating `Total_Demand_<p>` at early times would return final values instead of the correct historical values, causing:
- Early-period Order Basket showing demand that shouldn't exist yet
- Premature product deliveries for inactive sectors/products  
- Corrupted revenue calculations based on incorrect demand flows

**Solution**: Real-time KPI capture during the stepwise loop. The runner now captures KPI values immediately after updating gateway values and before advancing the model. These historical values are stored and used by the KPI extractor instead of post-run model evaluation, ensuring accurate time-series data that reflects actual simulation dynamics.

**Impact**: Resolves three critical issues:
1. Correct early-period demand values (Order Basket shows 0.0 when expected)
2. Proper product delivery timing (no premature deliveries for inactive products)
3. Accurate Active Projects KPI (fixed by reordering agent project completion logic)

## KPI Extraction & Outputs (Phase 15)
- Extract per-step series for:
  - **Revenue**: Total, by sector (market), and by product (sum of anchor + direct where applicable).
  - **Anchor Leads**: total + per sector (`CPC_<sector>` as appropriate). In SM-mode the runner computes per-sector leads by summing `Anchor_Lead_Generation_<s>_<p>` converters when `Anchor_Lead_Generation_<s>` is not built.
  - **Active Projects**: computed aggregator (from sector triggers × projects-per-agent proxy) or enhanced to count agent states if desired.
  - **Anchor Clients**: total + per sector (from active-agent proxy or agent counts if enabled in-loop).
  - **Other Leads/Clients**: Other Leads total only (product-driven aggregation); per-sector Other Leads rows are not emitted. Other Clients remain per product.
  - **Order Basket/Delivery**: per product using `Total_Demand` and delivery flows.
- Output: CSV named `Product_Growth_System_Complete_Results.csv`, columns `[Output Stocks, labels...]` where labels are derived from the runspecs grid.
 - Phase 17.6 (optional granularity): When run with flags `--kpi-sm-revenue-rows` and/or `--kpi-sm-client-rows`, the runner appends diagnostic rows `Revenue <sector> <product>` and/or `Anchor Clients <sector> <product>` to the CSV. Defaults leave the CSV surface unchanged.
- ABM metrics requirement (no fallback): The KPI extractor (`extract_and_write_kpis`) requires a per-step ABM metrics list (`agent_metrics_by_step`) with at least as many entries as emitted steps (typically 28). Each entry must include: `t` (float), `active_by_sector` (dict[str,int]), `inprogress_by_sector` (dict[str,int]), `active_total` (int), `inprogress_total` (int). If you do not track ABM state externally, supply a zero-initialized list to emit agent-based KPI rows as zeros. The lower-level collector `collect_kpis_for_step` mandates `step_idx` and `agent_metrics_by_step` and will raise if metrics are missing or out-of-range.

## Logging, Validation, and UI Runner
- **Scenario echo**: dump applied overrides (constants/points) and flag unknown keys.
- **Gateway checks**: per step, sample-log first N steps of `Agent_Demand_Input_<product>` values and totals.
- **Creation checks**: per step, log `Agents_To_Create_<sector>`, created count, cumulative.
- **Capacity & revenue sanity**: log utilization snapshots and period revenue sums; confirm `Total_Revenue ≈ Anchor + Client`.
- **Extraction safeguards**: missing columns default to zeros with warnings; include summary of non-found elements.
  - **UI runner**: Runner tab is controls-only (Validate, Start/Stop, status). Results are previewed in a dedicated Results tab. For UI-initiated runs, plots and optional KPI granularity (SM revenue rows and SM client rows) are enabled by default; debug logging remains optional. Packaging provides `make` targets and an optional Dockerfile for the UI layer.

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
  optional extra (sector, product) pairs. This ensures the UI only exposes
  valid, model-backed names.

- `validate_scenario_dict(bundle, scenario_dict)`
  Validates an in-memory scenario dict (no disk IO) and returns the same
  `Scenario` object as the file-based loader, enabling UI validation before save.

- `summarize_lists(bundle)`
  Returns market/sector/product lists and the sector→products mapping for UI
  dropdowns and context.

These helpers surface existing validation/naming logic to the UI and do not
modify model or runner behavior.

### Per-(sector, product) parameters by mode (quick reference)

Compact reference of which per-(s,p) anchor parameters are exposed in the UI depending on the run mode. In all cases, defaults can be provided in `inputs.json → anchor_params_sm`, and scenarios may override via `overrides.constants` using canonical names from `anchor_constant_sm(param, sector, product)`.

| Parameter (per‑(s,p)) | Sector mode (anchor_mode = "sector") | SM mode (anchor_mode = "sm") | Notes |
| --- | --- | --- | --- |
| initial_requirement_rate | Visible per‑(s,p) | Visible per‑(s,p) | Requirement family allowed in both modes |
| initial_req_growth | Visible per‑(s,p) | Visible per‑(s,p) |  |
| ramp_requirement_rate | Visible per‑(s,p) | Visible per‑(s,p) |  |
| ramp_req_growth | Visible per‑(s,p) | Visible per‑(s,p) |  |
| steady_requirement_rate | Visible per‑(s,p) | Visible per‑(s,p) |  |
| steady_req_growth | Visible per‑(s,p) | Visible per‑(s,p) |  |
| ramp_requirement_rate_override | Visible per‑(s,p) | Visible per‑(s,p) | Override for phase transitions |
| steady_requirement_rate_override | Visible per‑(s,p) | Visible per‑(s,p) | Override for phase transitions |
| requirement_to_order_lag | Visible per‑(s,p) | Visible per‑(s,p) | Sector‑mode falls back to sector‑level if per‑(s,p) absent |
| requirement_limit_multiplier | Visible per‑(s,p) | Visible per‑(s,p) | Requirement growth limit as multiplier of initial rate |
| anchor_start_year | Not per‑(s,p) (sector‑level only) | Visible per‑(s,p) | Full per‑(s,p) set only in SM mode |
| anchor_client_activation_delay | Not per‑(s,p) | Visible per‑(s,p) |  |
| anchor_lead_generation_rate | Not per‑(s,p) | Visible per‑(s,p) |  |
| lead_to_pc_conversion_rate | Not per‑(s,p) | Visible per‑(s,p) |  |
| project_generation_rate | Not per‑(s,p) | Visible per‑(s,p) |  |
| max_projects_per_pc | Not per‑(s,p) | Visible per‑(s,p) |  |
| project_duration | Not per‑(s,p) | Visible per‑(s,p) |  |
| projects_to_client_conversion | Not per‑(s,p) | Visible per‑(s,p) |  |
| initial_phase_duration | Not per‑(s,p) | Visible per‑(s,p) |  |
| ramp_phase_duration | Not per‑(s,p) | Visible per‑(s,p) |  |
| ATAM | Not per‑(s,p) | Visible per‑(s,p) |  |

UI note: After applying proposed sector→product mappings in the Primary Map editor, the Constants tab expands its permissible list to include those pairs. Sector mode shows only the requirement_* family per‑(s,p); SM mode exposes the full per‑(s,p) anchor set above.

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
- Requirement generation per AC (per primary product): Implemented inside agents with initial/ramp/steady phases and sector parameters, mapped 1:1 to the spec.
- Requirement→Order lag per sector and product: Supported by computing per-sector, per-product orders with `Material_Orders_<s>_<p> = delay(model, Agent_Demand_<s>_<p>, requirement_to_order_lag_<s>_<p>)`. If `<s>_<p>` is not provided in inputs, the model uses the sector-level `requirement_to_order_lag_<s>` as a fallback (Phase 16 precedence).
- Capacity-capped fulfillment: Implemented as `Anchor_Delivery_Flow_<p> = min(sum_s Material_Orders_<s>_<p>, max_capacity_lookup_<p>)` and `Client_Fulfilment` as per spec (see equations below). This matches the spec’s MIN-at-fulfillment logic.
- General lead-gen & direct client orders: Implemented as SD per product with discrete client conversion, order delays, fulfillment delay, and capacity limits. Number of leads is capped by TAM{product}
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

 - Direct clients per product p (discrete conversion with cohort aging):
  - `Inbound_Leads_<p> = inbound_lead_generation_rate_<p> * If(time >= lead_start_year_<p>, 1, 0) * If(CL_<p> < TAM_<p>, 1, 0)`
  - `Outbound_Leads_<p>` analogous; `CL_<p>` accumulates inbound + outbound.
  - `Total_New_Leads_<p> = Inbound_Leads_<p> + Outbound_Leads_<p>`
  - `Fractional_Client_Conversion_<p> = Total_New_Leads_<p> * lead_to_c_conversion_rate_<p>`
  - `Potential_Clients_<p>` stock accumulates fractional conversions minus `Client_Creation_<p>`
  - `Client_Creation_<p> = max(0, round(Potential_Clients_<p> - 0.5, 0))`
  - `C_<p>` accumulates `Client_Creation_<p>`
  - **NEW: Cohort aging chain**: `Direct_Client_Cohort_0_<p>`, `Direct_Client_Cohort_1_<p>`, ... (one bucket per simulated quarter)
    - `Direct_Client_Cohort_0_<p>`: d/dt = `Client_Creation_Drain_<p>` - (1/dt) * `Direct_Client_Cohort_0_<p>`
    - `Direct_Client_Cohort_a_<p>`: d/dt = (1/dt) * `Direct_Client_Cohort_{a-1}_<p>` - (1/dt) * `Direct_Client_Cohort_a_<p>` (for a > 0)
    - Terminal bucket accumulates remaining clients without outflow
  - **NEW: Per-cohort order calculation**: `per_client_order_a = min(avg_order_quantity_initial_<p> + (avg_order_quantity_initial_<p> * client_requirement_growth_<p>) * a, avg_order_quantity_initial_<p> * requirement_limit_multiplier_<p>)`
  - **NEW: Total cohort orders**: `Cohort_Effective_Orders_<p> = sum_over_ages(Direct_Client_Cohort_a_<p> * per_client_order_a)`
  - `Client_Requirement_<p> = delay(model, Cohort_Effective_Orders_<p>, lead_to_requirement_delay_<p>)`

- Capacity & lookups per product p:
  - `max_capacity_lookup_<p> = lookup(time, max_capacity_<p>)`
  - `Price_<p> = lookup(time, price_<p>)`

- ABM→SD gateway per sector–product (s,p):
  - `Agent_Demand_Sector_Input_<s>_<p>` is a converter with a numeric equation updated per step by the runner (no dependencies).
  - `Agent_Aggregated_Demand_<p> = sum_over_sectors_s(Agent_Demand_Sector_Input_<s>_<p>)`
  - `Total_Demand_<p> = Agent_Aggregated_Demand_<p> + Client_Requirement_<p>`
  - `Fulfillment_Ratio_<p> = min(1, If(Total_Demand_<p> > 0, max_capacity_lookup_<p> / Total_Demand_<p>, 1))`

 - Deliveries:
  - Anchor (per sector with sector–product lag L_{s,p}): For each sector s that uses p,
    - `Delayed_Agent_Demand_<s>_<p> = Agent_Demand_Sector_Input_<s>_<p> * Fulfillment_Ratio_<p>`
    - `Anchor_Delivery_Flow_<s>_<p> = delay(model, Delayed_Agent_Demand_<s>_<p>, requirement_to_order_lag_<s>_<p>)`
    - `Anchor_Delivery_Flow_<p> = sum_over_sectors_s( Anchor_Delivery_Flow_<s>_<p> )`
  - Client delivery: `Client_Delivery_Flow_<p> = delay(model, Delayed_Client_Demand_<p>, requirement_to_fulfilment_delay_<p>)`
    - `Delayed_Client_Demand_<p> = Client_Requirement_<p> * Fulfillment_Ratio_<p>`

**Delay Implementation Note**: BPTK_Py's `F.delay()` function has a one-step offset behavior where input at time T produces output at time T + delay + 1 step. To achieve intuitive delay behavior (input at time T produces output at time T + delay), the model automatically applies a correction by subtracting 1 from all delay parameters. This is handled transparently by the `_apply_delay_with_offset()` helper function, so users can specify delay parameters normally without needing to account for the BPTK_Py timing behavior.

- Revenue:
  - Sector-level anchor revenue: `Anchor_Revenue_<s>_<p> = Anchor_Delivery_Flow_<s>_<p> * Price_<p>` and `Anchor_Revenue_<s> = sum_p(Anchor_Revenue_<s>_<p>)`
  - Product-level revenues: `Anchor_Revenue_<p> = sum_s(Anchor_Revenue_<s>_<p>)`; `Client_Revenue_<p> = Client_Delivery_Flow_<p> * Price_<p>`
  - Totals: `Anchor_Revenue = sum_p(Anchor_Revenue_<p>)`; `Client_Revenue = sum_p(Client_Revenue_<p>)`; `Total_Revenue = Anchor_Revenue + Client_Revenue`

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
sys.add_gateway_converters_for_all_products()
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

  # aggregate agent demand by product p
  for each product p:
    agg[p] = sum(a.requirements[p] for all agents)
    set_equation(sys, "Agent_Demand_Input_<p>", agg[p])

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
- Revenue by sector s: `Anchor_Revenue_<s>` (sum over products of sector anchor revenue only) → row: `Revenue <s>`
- Revenue by product p: `Anchor_Revenue_<p> + Client_Revenue_<p>` → row: `Revenue <p>`
- Anchor Leads total: sum of `CPC_<s>` changes per quarter → row: `Anchor Leads`
- Anchor Leads by sector s: `CPC_<s>` → row: `Anchor Leads <s>`
- Active Projects total: proxy or agent-state count; default proxy = sum over s `(Agent_Creation_Trigger_<s> * max_projects_per_pc_<s>)` → row: `Active Projects`
- Active Projects by sector s: zero rows (as per expected format) or extend later.
- Anchor Clients total: `Total_Active_Anchor_Clients` (proxy or agent-state count) → row: `Anchor Clients`
- Anchor Clients by sector s: `Active_Anchor_Clients_<s>` → row: `Anchor Clients <s>`
- Other Leads total: sum over products of `CL_<p>` increments, reported per quarter (divide SD evaluation by 4) → row: `Other Leads`
  
- Other Clients by product p: `C_<p>` → row: `Other Clients <p>`
- Order Basket by product p: `Total_Demand_<p>` → row: `Order Basket <p>`
- Order Delivery by product p: `Anchor_Delivery_Flow_<p> + Client_Delivery_Flow_<p>` → row: `Order Delivery <p>`

## Quarter Labeling & Time Grid (Phase 15)
- Time grid: `[starttime + i*dt for i in 0..num_steps-1]` with arbitrary positive `dt`.
- Output periods: one column per simulated step; labels derived from each absolute time by mapping fractional year to nearest quarter (Q1=.00, Q2=.25, Q3=.50, Q4=.75).
- No fixed 28-step padding or truncation.

## Validation & Acceptance Checklist
- Data load: all required sectors/products present across JSON sections; fail on missing coverage.
- Lists contain `'US'` market (US-only scope in this phase).
- Root contains `'lists'` key.
- Equations: delays use quarters directly (no dt scaling); lookups accept 0 values without NaN.
- Agent creation: per-step `Agents_To_Create_<s>` non-negative integer; accumulator drains via outflow.
- Gateways: non-negative values; logged snapshots for first and mid/last steps.
- Capacity utilization: `Fulfillment_Ratio_<p> ∈ [0,1]`.
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


