## Growth System — Systems Elements and Interactions (System Dynamics View)

### Purpose and scope
This document formalizes the hybrid SD+ABM model in standard System Dynamics terms. It inventories stocks, flows, converters, lookups, delays, and ABM→SD gateways; describes interactions; and provides causal loop and stock–flow overview diagrams. Naming follows the implementation and `technical_architecture.md`. Time base is years with dt = 0.25 years (quarters). Rates specified “per quarter” are handled explicitly without hidden dt scaling.

### Notation
- Stocks: capitalized nouns (e.g., `CPC_<sector>`, `C_<material>`)
- Flows: verbs/noun-phrases often with “Flow” suffix (e.g., `Client_Delivery_Flow_<m>`)
- Converters: rates, parameters, algebraic equations (e.g., `lead_to_c_conversion_rate_<m>`, `Fulfillment_Ratio_<m>`, `Total_Demand_<m>`)
- Lookups: time-varying tables `price_<m>`, `max_capacity_<m>` exposed as converters `Price_<m>`, `max_capacity_lookup_<m>`
- Delays: `delay(model, x, τ)` where τ is in quarters (no dt scaling applied)
- Gateways: numeric per-step ABM→SD inputs `Agent_Demand_Sector_Input_<s>_<m>` and their aggregations

---

## Element inventory

### Anchor channel (per sector s)
- Stocks
  - `CPC_<s>`: cumulative potential anchor clients (integrates `Anchor_Lead_Generation_<s>`) [unit: clients]
  - `Agent_Creation_Accumulator_<s>`: fractional potential clients pending integer “fires” [clients]
  - `Cumulative_Agents_Created_<s>`: monitoring stock of created agents [clients]
- Flows/Converters
  - `Anchor_Lead_Generation_<s> = 4 * anchor_lead_generation_rate_<s> * If(Time ≥ anchor_start_year_<s>,1,0) * If(CPC_<s> < ATAM_<s>,1,0)` [clients/year]
  - `New_PC_Flow_<s> = Anchor_Lead_Generation_<s> * lead_to_pc_conversion_rate_<s>` [clients/year]
  - `Agent_Creation_Inflow_<s> = New_PC_Flow_<s>` (converter feeding stock derivative)
  - `Agent_Creation_Outflow_<s> = max(0, floor_like(Agent_Creation_Accumulator_<s>))` [clients/quarter-equivalent]
  - `Agent_Creation_Drain_<s> = 4 * Agent_Creation_Outflow_<s>` ensures one whole client per quarter step drains from the accumulator
  - `Agents_To_Create_<s> = Agent_Creation_Outflow_<s>` (integer creations in current step)
- ABM coupling (per sector–material)
  - `Agent_Demand_Sector_Input_<s>_<m>`: numeric gateway set each step by ABM aggregation [units: material per quarter]
  - `Delayed_Agent_Demand_<s>_<m> = Agent_Demand_Sector_Input_<s>_<m> * Fulfillment_Ratio_<m>`
  - `Anchor_Delivery_Flow_<s>_<m> = delay(model, Delayed_Agent_Demand_<s>_<m>, requirement_to_order_lag_<s>_<m>)`
  - `Anchor_Delivery_Flow_<m> = Σ_s Anchor_Delivery_Flow_<s>_<m>`

SM‑mode ABM (per pair s,m)
- In SM‑mode (Phase 17.2/17.3), creation pipelines are built per (s,m) and agents are instantiated per pair.
- `AnchorClientAgentSM` is a per‑(s,m) ABM with lifecycle POTENTIAL → PENDING_ACTIVATION → ACTIVE and per‑phase requirements (initial, ramp, steady). Requirements are produced only when ACTIVE and after `anchor_start_year_<s>_<m>`.
- Factory `build_sm_anchor_agent_factory(sector, material)` constructs agents strictly from `anchor_params_sm` values for the pair.
 - Runner (Phase 17.4/17.5) instantiates per-step using `Agents_To_Create_<s>_<m>`, supports SM seeding at t0 (initializes `CPC_<s>_<m>` and `Cumulative_Agents_Created_<s>_<m>` where present), and aggregates demand directly into `Agent_Demand_Sector_Input_<s>_<m>`. Sector-level creation and seeding are disallowed in SM-mode.

### Direct clients channel (per material m)
- Stocks
  - `CL_<m>`: cumulative leads for TAM gating [leads]
  - `Potential_Clients_<m>`: accumulator for fractional client conversions [clients]
  - `C_<m>`: cumulative discrete clients created [clients]
- Flows/Converters
  - `Inbound_Leads_<m> = 4 * inbound_lead_generation_rate_<m> * If(Time ≥ lead_start_year_<m>,1,0) * If(CL_<m> < TAM_<m>,1,0)` [leads/year]
  - `Outbound_Leads_<m>` analogous
  - `Total_New_Leads_<m> = Inbound_Leads_<m> + Outbound_Leads_<m>`
  - `Fractional_Client_Conversion_<m> = Total_New_Leads_<m> * lead_to_c_conversion_rate_<m>`
  - `Client_Creation_<m> = max(0, floor_like(Potential_Clients_<m>))` [clients/quarter-equivalent]
  - `Client_Creation_Drain_<m> = 4 * Client_Creation_<m>`; `Potential_Clients_<m> = Fractional_Client_Conversion_<m> - Client_Creation_Drain_<m>`
  - `C_<m>` integrates `Client_Creation_Drain_<m>`
  - `avg_order_quantity_<m> = avg_order_quantity_initial_<m> * (1 + client_requirement_growth_<m>)^(quarters_since_start)`
  - `Client_Requirement_<m> = delay(model, C_<m> * avg_order_quantity_<m>, lead_to_requirement_delay_<m>)`
  - `Delayed_Client_Demand_<m> = Client_Requirement_<m> * Fulfillment_Ratio_<m>`
  - `Client_Delivery_Flow_<m> = delay(model, Delayed_Client_Demand_<m>, requirement_to_fulfilment_delay_<m>)`

### Capacity, demand aggregation, pricing, revenue (per material m)
- Lookups → Converters
  - `max_capacity_lookup_<m> = lookup(Time, max_capacity_<m>) / 4` [per quarter]
  - `Price_<m> = lookup(Time, price_<m>)` [currency/unit]
- Aggregation & fulfillment
  - `Agent_Aggregated_Demand_<m> = Σ_s Agent_Demand_Sector_Input_<s>_<m>`
  - `Total_Demand_<m> = Agent_Aggregated_Demand_<m> + Client_Requirement_<m>`
  - `Fulfillment_Ratio_<m> = min(1, If(Total_Demand_<m> > 0, max_capacity_lookup_<m> / Total_Demand_<m>, 1))`
- Revenue
  - `Anchor_Revenue_<s>_<m> = Anchor_Delivery_Flow_<s>_<m> * Price_<m>`
  - `Anchor_Revenue_<m> = Σ_s Anchor_Revenue_<s>_<m>`; `Client_Revenue_<m> = Client_Delivery_Flow_<m> * Price_<m>`
  - `Total_Revenue = Σ_m (Anchor_Delivery_Flow_<m> + Client_Delivery_Flow_<m>) * Price_<m>`

### Delays (quarters; no dt scaling)
- `lead_to_requirement_delay_<m>` (direct clients)
- `requirement_to_fulfilment_delay_<m>` (direct clients)
- `requirement_to_order_lag_<s>_<m>` (anchor sector–material ordering; falls back to sector-level when per-(s,m) not provided in sector-mode; SM‑mode requires per‑(s,m) values with no fallback)

### Primary map overrides and seeding (UI Phases 6–8)
- Primary map overrides: The UI can propose replacements to the sector→materials mapping by providing, per sector, a list of `{material, start_year}` entries. Validation ensures sectors/materials exist and materials are present across parameter tables; `start_year` must be numeric. Overrides replace the sector’s mapping atomically. Packaging updates add a Makefile and optional UI container without altering equations.
- Seeding: The UI supports seeds for ACTIVE anchor clients per sector (and per (sector, material) in SM‑mode) and direct clients per material. Seeds are validated as non‑negative integers and must reference known sectors/materials. Seeding affects initial stock values and agent instantiation at t0; equations remain unchanged.

---

## Interaction map and feedback structure

### Core interactions (per material)
- ABM demand (anchor) + SD demand (direct) → `Total_Demand_<m>`
- `Total_Demand_<m>` and `max_capacity_lookup_<m>` → `Fulfillment_Ratio_<m>`
- `Fulfillment_Ratio_<m>` limits both channels’ delivered flows → revenue

### Gating/balancing effects
- ATAM gating (anchor): `CPC_<s> < ATAM_<s>` balances further anchor lead generation
- TAM gating (direct): `CL_<m> < TAM_<m>` balances further leads → clients
- Capacity constraint: `Fulfillment_Ratio_<m> ≤ 1` balances unrealized demand

### Growth/reinforcement patterns (within-channel)
- Direct clients: average order quantity grows geometrically per quarter via `client_requirement_growth_<m>` producing within-client reinforcing demand growth (exogenous parameter driven)
- Anchor clients: three-phase requirement growth per client once ACTIVE (initial → ramp → steady), parameterized per sector

---

## Causal Loop Diagram (CLD) — high-level
```mermaid
graph TD
  A[Anchor Leads (per sector)] -->|+ via conversion| B[Potential Anchor Clients]
  B -->|accumulate & fire| C[Active Anchor Clients (ABM agents)]
  C -->|per-phase requirements| D[Anchor Demand by Material]
  E[Direct Leads (per material)] -->|+ via conversion| F[Direct Clients]
  F -->|avg basket growth| G[Direct Client Requirement]
  D --> H[Total Demand per Material]
  G --> H
  H --> I[Fulfillment Ratio]
  I --> J[Anchor Deliveries]
  I --> K[Client Deliveries]
  J --> L[Revenue (Anchor)]
  K --> M[Revenue (Client)]
  subgraph Balancing Limits
    N[ATAM per sector] -. limits .-> A
    O[TAM per material] -. limits .-> E
    P[Capacity Lookup per material] -. caps .-> I
  end
```

Notes: Signs (+/limits) indicate polarities; revenue has no modeled feedback into rates in this phase.

---

## Stock–Flow overview (per material)
```mermaid
flowchart LR
  %% Direct channel
  subgraph Direct_Clients_SD
    CL[Stock: CL_<m>] -- Inbound/Outbound Leads --> CL
    PC[Stock: Potential_Clients_<m>] -- +Fractional Conversion --> PC
    CC[Flow: Client_Creation_<m>] --> CStock[Stock: C_<m>]
    CStock -- * avg_order_quantity_<m> --> Req[Client_Requirement_<m>]
    Req -- * Fulfillment_Ratio_<m> --> DCD[Delayed_Client_Demand_<m>] -->|delay τ_cf| CDF[Client_Delivery_Flow_<m>]
  end

  %% Anchor channel
  subgraph Anchor_ABM_to_SD
    CPC[Stock: CPC_<s>] -- Anchor_Lead_Generation_<s> --> CPC
    ACC[Stock: Agent_Creation_Accumulator_<s>] -->|drain (Agents_To_Create_<s>)| ACC
    GW[Gateway: Agent_Demand_Sector_Input_<s>_<m>] -.-> FR[Fulfillment_Ratio_<m>]
    GW -->|* FR| DAD[Delayed_Agent_Demand_<s>_<m>] -->|delay τ_s| ADFsm[Anchor_Delivery_Flow_<s>_<m>]
  end

  %% Aggregation, capacity, revenue
  GW --> Agg[Agent_Aggregated_Demand_<m>]
  Req --> TD[Total_Demand_<m>]
  Agg --> TD
  TD --> FR
  FR --> ADFm[Anchor_Delivery_Flow_<m>]
  CDF --> RevM[Revenue_<m>]
  ADFm --> RevM
```

Legend: τ_cf = `requirement_to_fulfilment_delay_<m>`, τ_s = `requirement_to_order_lag_<s>_<m>`.

---

## Equations summary (canonical forms)
- Gated lead generation (anchor): `Anchor_Lead_Generation_<s>` per above; `CPC_<s>` integrates it
- Accumulate–fire (integerization) uses `floor_like(x) = Round(x − 0.5, 0)` and drains by ×4 to achieve integer-per-quarter behavior with dt=0.25
- Direct client requirement: `delay(model, C_<m> * avg_order_quantity_<m>, lead_to_requirement_delay_<m>)`
- Fulfillment: `Fulfillment_Ratio_<m> = min(1, If(Total_Demand_<m> > 0, max_capacity_lookup_<m> / Total_Demand_<m>, 1))`
- Deliveries: channel demand × `Fulfillment_Ratio_<m>` passed through appropriate delay
- Revenue: deliveries × price per material, aggregated

Units: delays and durations in quarters; Time axis is years; lookups read yearly tables; capacity is converted to per-quarter.

---

## ABM→SD gateway contract
- Runner updates `Agent_Demand_Sector_Input_<s>_<m>` each step with aggregated per-step anchor requirements from active agents
- KPIs that depend on gateways are captured during the step (prior to advancing the scheduler) to avoid post-run gateway state corruption
 - Phase 17.6 (optional diagnostics): When CLI flags are provided, the runner also emits per‑(sector, material) KPI rows for `Revenue <sector> <material>` and `Anchor Clients <sector> <material>`. These do not alter core equations or totals and remain disabled by default.

---

## Assumptions and limits
- No endogenous capacity investment; capacity is exogenous via lookup
- No feedback from revenue to demand rates in this phase
- Material start years gate anchor agent production by sector–material mapping
- Direct leads and anchor leads are independently gated by TAM/ATAM respectively

---

## How to extend
- Endogenize capacity: add `Capacity_Investment` flow and a stock for `Installed_Capacity_<m>` feeding the lookup or replacing it
- Feedback from revenue to marketing: e.g., `Revenue` → `inbound_lead_generation_rate_<m>` as a reinforcing loop with saturation
- Sector–material specific lags: already supported; extend to material-specific ATAM if needed

---

## Cross-reference
- See `technical_architecture.md` for canonical element names and parameter taxonomy
- See `src/growth_model.py` for SD build and equations, `src/abm_anchor.py` for agent logic, and `simulate_growth.py` for stepwise coupling and KPI capture


