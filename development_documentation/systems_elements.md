## Product Growth System — Systems Elements and Interactions (System Dynamics View)

### Purpose and scope
This document formalizes the hybrid SD+ABM model in standard System Dynamics terms. It inventories stocks, flows, converters, lookups, delays, and ABM→SD gateways; describes interactions; and provides causal loop and stock–flow overview diagrams. Naming follows the implementation and `technical_architecture.md`. Time base is years with dt = 0.25 years (quarters). Rates specified "per quarter" are handled explicitly without hidden dt scaling.

The system is designed to be industry-agnostic, allowing you to model any sectors and products by configuring the inputs. No hard-coded industry assumptions are made.

### Notation
- Stocks: capitalized nouns (e.g., `CPC_<sector>`, `C_<product>`)
- Flows: verbs/noun-phrases often with "Flow" suffix (e.g., `Client_Delivery_Flow_<p>`)
- Converters: rates, parameters, algebraic equations (e.g., `lead_to_c_conversion_rate_<p>`, `Fulfillment_Ratio_<p>`, `Total_Demand_<p>`)
- Lookups: time-varying tables `price_<p>`, `max_capacity_<p>` exposed as converters `Price_<p>`, `max_capacity_lookup_<p>`
- Delays: `delay(model, x, τ)` where τ is in quarters (no dt scaling applied)
- Gateways: numeric per-step ABM→SD inputs `Agent_Demand_Sector_Input_<s>_<p>` and their aggregations

---

## Element inventory

### Anchor channel (per sector s)
- Stocks
  - `CPC_<s>`: cumulative potential anchor clients (integrates `Anchor_Lead_Generation_<s>`) [unit: clients]
  - `Agent_Creation_Accumulator_<s>`: fractional potential clients pending integer "fires" [clients]
  - `Cumulative_Agents_Created_<s>`: monitoring stock of created agents [clients]
- Flows/Converters
  - `Anchor_Lead_Generation_<s> = 4 * anchor_lead_generation_rate_<s> * If(Time ≥ anchor_start_year_<s>,1,0) * If(CPC_<s> < ATAM_<s>,1,0)` [clients/year]
  - `New_PC_Flow_<s> = Anchor_Lead_Generation_<s> * lead_to_pc_conversion_rate_<s>` [clients/year]
  - `Agent_Creation_Inflow_<s> = New_PC_Flow_<s>` (converter feeding stock derivative)
  - `Agent_Creation_Outflow_<s> = max(0, floor_like(Agent_Creation_Accumulator_<s>))` [clients/quarter-equivalent]
  - `Agent_Creation_Drain_<s> = 4 * Agent_Creation_Outflow_<s>` ensures one whole client per quarter step drains from the accumulator
  - `Agents_To_Create_<s> = Agent_Creation_Outflow_<s>` (integer creations in current step)
- ABM coupling (per sector–product)
  - `Agent_Demand_Sector_Input_<s>_<p>`: numeric gateway set each step by ABM aggregation [units: product per quarter]
  - `Delayed_Agent_Demand_<s>_<p> = Agent_Demand_Sector_Input_<s>_<p> * Fulfillment_Ratio_<p>`
  - `Anchor_Delivery_Flow_<s>_<p> = delay(model, Delayed_Agent_Demand_<s>_<p>, requirement_to_order_lag_<s>_<p>)`
  - `Anchor_Delivery_Flow_<p> = Σ_s Anchor_Delivery_Flow_<s>_<p>`

SM‑mode ABM (per pair s,p)
- In SM‑mode (Phase 17.2/17.3), creation pipelines are built per (s,p) and agents are instantiated per pair.
- `AnchorClientAgentSM` is a per‑(s,p) ABM with lifecycle POTENTIAL → PENDING_ACTIVATION → ACTIVE and per‑phase requirements (initial, ramp, steady). Requirements are produced only when ACTIVE and after `anchor_start_year_<s>_<p>`.
- Factory `build_sm_anchor_agent_factory(sector, product)` constructs agents strictly from `anchor_params_sm` values for the pair.
 - Runner (Phase 17.4/17.5) instantiates per-step using `Agents_To_Create_<s>_<p>`, supports SP seeding at t0 (initializes `CPC_<s>_<p>` and `Cumulative_Agents_Created_<s>_<p>` where present), and aggregates demand directly into `Agent_Demand_Sector_Input_<s>_<p>`. Sector-level creation and seeding are disallowed in SM-mode.

### Direct clients channel (per product p) — **NEW: Cohort-based system**
- Stocks
  - `CL_<p>`: cumulative leads for TAM gating [leads]
  - `Potential_Clients_<p>`: accumulator for fractional client conversions [clients]
  - `C_<p>`: cumulative discrete clients created [clients]
  - **NEW: Cohort aging chain**: `Direct_Client_Cohort_0_<p>`, `Direct_Client_Cohort_1_<p>`, ... (one bucket per simulated quarter)
- Flows/Converters
  - `Inbound_Leads_<p> = 4 * inbound_lead_generation_rate_<p> * If(Time ≥ lead_start_year_<p>,1,0) * If(CL_<p> < TAM_<p>,1,0)` [leads/year]
  - `Outbound_Leads_<p>` analogous
  - `Total_New_Leads_<p> = Inbound_Leads_<p> + Outbound_Leads_<p>`
  - `Fractional_Client_Conversion_<p> = Total_New_Leads_<p> * lead_to_c_conversion_rate_<p>`
  - `Client_Creation_<p> = max(0, floor_like(Potential_Clients_<p>))` [clients/quarter-equivalent]
  - `Client_Creation_Drain_<p> = 4 * Client_Creation_<p>`; `Potential_Clients_<p> = Fractional_Client_Conversion_<p> - Client_Creation_Drain_<p>`
  - `C_<p>` integrates `Client_Creation_Drain_<p>`
  - **NEW: Cohort aging dynamics**: 
    - `Direct_Client_Cohort_0_<p>`: d/dt = `Client_Creation_Drain_<p>` - (1/dt) × `Direct_Client_Cohort_0_<p>`
    - `Direct_Client_Cohort_a_<p>`: d/dt = (1/dt) × `Direct_Client_Cohort_{a-1}_<p>` - (1/dt) × `Direct_Client_Cohort_a_<p>` (for a > 0)
    - Terminal bucket accumulates remaining clients without outflow
  - **NEW: Per-cohort order calculation**: `per_client_order_a = min(avg_order_quantity_initial_<p> + (avg_order_quantity_initial_<p> × client_requirement_growth_<p>) × a, avg_order_quantity_initial_<p> × requirement_limit_multiplier_<p>)`
  - **NEW: Total cohort orders**: `Cohort_Effective_Orders_<p> = Σ_a(Direct_Client_Cohort_a_<p> × per_client_order_a)`
  - `Client_Requirement_<p> = delay(model, Cohort_Effective_Orders_<p>, lead_to_requirement_delay_<p>)`
  - `Delayed_Client_Demand_<p> = Client_Requirement_<p> * Fulfillment_Ratio_<p>`
  - `Client_Delivery_Flow_<p> = delay(model, Delayed_Client_Demand_<p>, requirement_to_fulfilment_delay_<p>)`

### Capacity, demand aggregation, pricing, revenue (per product p)
- Lookups → Converters
  - `max_capacity_lookup_<p> = lookup(Time, max_capacity_<p>) / 4` [per quarter]
  - `Price_<p> = lookup(Time, price_<p>)` [currency/unit]
- Aggregation & fulfillment
  - `Agent_Aggregated_Demand_<p> = Σ_s Agent_Demand_Sector_Input_<s>_<p>`
  - `Total_Demand_<p> = Agent_Aggregated_Demand_<p> + Client_Requirement_<p>`
  - `Fulfillment_Ratio_<p> = min(1, If(Total_Demand_<p> > 0, max_capacity_lookup_<p> / Total_Demand_<p>, 1))`
- Revenue
  - `Anchor_Revenue_<s>_<p> = Anchor_Delivery_Flow_<s>_<p> * Price_<p>`
  - `Anchor_Revenue_<p> = Σ_s Anchor_Revenue_<s>_<p>`; `Client_Revenue_<p> = Client_Delivery_Flow_<p> * Price_<p>`
  - `Total_Revenue = Σ_p (Anchor_Delivery_Flow_<p> + Client_Delivery_Flow_<p>) * Price_<p>`

### Delays (quarters; no dt scaling)
- `lead_to_requirement_delay_<p>` (direct clients)
- `requirement_to_fulfilment_delay_<p>` (direct clients)
- `requirement_to_order_lag_<s>_<p>` (anchor sector–product ordering; falls back to sector-level when per-(s,p) not provided in sector-mode; SM‑mode requires per‑(s,p) values with no fallback)

**Note**: The model automatically corrects for BPTK_Py's delay function timing behavior to ensure intuitive delay behavior. When you specify a 1-quarter delay, you get exactly 1-quarter delay timing. This correction is handled transparently by the `_apply_delay_with_offset()` helper function.

### Primary map overrides and seeding (UI Phases 6–8)
- Primary map overrides: The UI can propose replacements to the sector→products mapping by providing, per sector, a list of `{product, start_year}` entries. Validation ensures sectors/products exist and products are present across parameter tables; `start_year` must be numeric. Overrides replace the sector's mapping atomically. Packaging updates add a Makefile and optional UI container without altering equations.
- Seeding: The UI supports seeds for ACTIVE anchor clients per sector (and per (sector, product) in SM‑mode) and direct clients per product. Seeds are validated as non‑negative integers and must reference known sectors/products. Seeding affects initial stock values and agent instantiation at t0; equations remain unchanged.

---

## Interaction map and feedback structure

### Core interactions (per product)
- ABM demand (anchor) + SD demand (direct) → `Total_Demand_<p>`
- `Total_Demand_<p>` and `max_capacity_lookup_<p>` → `Fulfillment_Ratio_<p>`
- `Fulfillment_Ratio_<p>` limits both channels' delivered flows → revenue

### Gating/balancing effects
- ATAM gating (anchor): `CPC_<s> < ATAM_<s>` balances further anchor lead generation
- TAM gating (direct): `CL_<p> < TAM_<p>` balances further leads → clients
- Capacity constraint: `Fulfillment_Ratio_<p> ≤ 1` balances unrealized demand

### Growth/reinforcement patterns (within-channel)
- **NEW: Direct clients cohort system**: Each cohort starts with base order quantity and grows linearly over time via `client_requirement_growth_<p>`, with per-client order limits via `requirement_limit_multiplier_<p>`. This produces realistic cohort-based growth where newer clients start at base rates and older cohorts have higher per-client orders, but with hard caps to prevent unlimited growth.
- Anchor clients: three-phase requirement growth per client once ACTIVE (initial → ramp → steady), parameterized per sector, with optional growth limits via `requirement_limit_multiplier` to prevent unlimited growth

---

## Causal Loop Diagram (CLD) — high-level
```mermaid
graph TD
  A[Anchor Leads (per sector)] -->|+ via conversion| B[Potential Anchor Clients]
  B -->|accumulate & fire| C[Active Anchor Clients (ABM agents)]
  C -->|per-phase requirements| D[Anchor Demand by Product]
  E[Direct Leads (per product)] -->|+ via conversion| F[Direct Clients]
  F -->|cohort aging + linear growth| G[Direct Client Requirement]
  D --> H[Total Demand per Product]
  G --> H
  H --> I[Fulfillment Ratio]
  I --> J[Anchor Deliveries]
  I --> K[Client Deliveries]
  J --> L[Revenue (Anchor)]
  K --> M[Revenue (Client)]
  subgraph Balancing Limits
    N[ATAM per sector] -. limits .-> A
    O[TAM per product] -. limits .-> E
    P[Capacity Lookup per product] -. caps .-> I
  end
```

Notes: Signs (+/limits) indicate polarities; revenue has no modeled feedback into rates in this phase.

---

## Stock–Flow overview (per product)
```mermaid
flowchart LR
  %% Direct channel
  subgraph Direct_Clients_SD
    CL[Stock: CL_<p>] -- Inbound/Outbound Leads --> CL
    PC[Stock: Potential_Clients_<p>] -- +Fractional Conversion --> PC
    CC[Flow: Client_Creation_<p>] --> CStock[Stock: C_<p>]
    CC --> Cohort0[Stock: Direct_Client_Cohort_0_<p>]
    Cohort0 --> Cohort1[Stock: Direct_Client_Cohort_1_<p>]
    Cohort1 --> CohortN[Stock: Direct_Client_Cohort_N_<p>]
    Cohort0 -- * per_client_order_0 --> CEO[Cohort_Effective_Orders_<p>]
    Cohort1 -- * per_client_order_1 --> CEO
    CohortN -- * per_client_order_N --> CEO
    CEO --> Req[Client_Requirement_<p>]
    Req -- * Fulfillment_Ratio_<p> --> DCD[Delayed_Client_Demand_<p>] -->|delay τ_cf| CDF[Client_Delivery_Flow_<p>]
  end

  %% Anchor channel
  subgraph Anchor_ABM_to_SD
    CPC[Stock: CPC_<s>] -- Anchor_Lead_Generation_<s> --> CPC
    ACC[Stock: Agent_Creation_Accumulator_<s>] -->|drain (Agents_To_Create_<s>)| ACC
    GW[Gateway: Agent_Demand_Sector_Input_<s>_<p>] -.-> FR[Fulfillment_Ratio_<p>]
    GW -->|* FR| DAD[Delayed_Agent_Demand_<s>_<p>] -->|delay τ_s| ADFsm[Anchor_Delivery_Flow_<s>_<p>]
  end

  %% Aggregation, capacity, revenue
  GW --> Agg[Agent_Aggregated_Demand_<p>]
  Req --> TD[Total_Demand_<p>]
  Agg --> TD
  TD --> FR
  FR --> ADFm[Anchor_Delivery_Flow_<p>]
  CDF --> RevM[Revenue_<p>]
  ADFm --> RevM
```

Legend: τ_cf = `requirement_to_fulfilment_delay_<p>`, τ_s = `requirement_to_order_lag_<s>_<p>`.

---

## Equations summary (canonical forms)
- Gated lead generation (anchor): `Anchor_Lead_Generation_<s>` per above; `CPC_<s>` integrates it
- Accumulate–fire (integerization) uses `floor_like(x) = Round(x − 0.5, 0)` and drains by ×4 to achieve integer-per-quarter behavior with dt=0.25
- **NEW: Direct client requirement (cohort-based)**: `delay(model, Cohort_Effective_Orders_<p>, lead_to_requirement_delay_<p>)` where `Cohort_Effective_Orders_<p> = Σ_a(Direct_Client_Cohort_a_<p> × per_client_order_a)`
- Fulfillment: `Fulfillment_Ratio_<p> = min(1, If(Total_Demand_<p> > 0, max_capacity_lookup_<p> / Total_Demand_<p>, 1))`
- Deliveries: channel demand × `Fulfillment_Ratio_<p>` passed through appropriate delay
- Revenue: deliveries × price per product, aggregated

Units: delays and durations in quarters; Time axis is years; lookups read yearly tables; capacity is converted to per-quarter.

---

## ABM→SD gateway contract
- Runner updates `Agent_Demand_Sector_Input_<s>_<p>` each step with aggregated per-step anchor requirements from active agents
- KPIs that depend on gateways are captured during the step (prior to advancing the scheduler) to avoid post-run gateway state corruption
 - Phase 17.6 (optional diagnostics): When CLI flags are provided, the runner also emits per‑(sector, product) KPI rows for `Revenue <sector> <product>` and `Anchor Clients <sector> <product>`. These do not alter core equations or totals and remain disabled by default.

---

## Assumptions and limits
- No endogenous capacity investment; capacity is exogenous via lookup
- No feedback from revenue to demand rates in this phase
- Product start years gate anchor agent production by sector–product mapping
- Direct leads and anchor leads are independently gated by TAM/ATAM respectively
- **NEW: Direct client cohort system**: Each cohort grows linearly with per-client order limits via `requirement_limit_multiplier_<p>` to prevent unlimited growth (hard stop when limit is reached)
- Anchor client requirement growth can be limited via `requirement_limit_multiplier` to prevent unlimited growth (hard stop when limit is reached)

---

## How to extend
- Endogenize capacity: add `Capacity_Investment` flow and a stock for `Installed_Capacity_<p>` feeding the lookup or replacing it
- Feedback from revenue to marketing: e.g., `Revenue` → `inbound_lead_generation_rate_<p>` as a reinforcing loop with saturation
- Sector–product specific lags: already supported; extend to product-specific ATAM if needed

---

## Cross-reference
- See `technical_architecture.md` for canonical element names and parameter taxonomy
- See `src/growth_model.py` for SD build and equations, `src/abm_anchor.py`