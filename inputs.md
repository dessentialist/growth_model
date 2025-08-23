## Model Inputs

This document lists all inputs the FFF Growth System consumes. It is organized by where and how the model uses them, and annotated with whether each input is sector-specific or material-specific. Values live primarily in `inputs.json`; scenario files can override many of them.

### Who updates it and where
- **Run controls (start/stop/dt)**: edit in the scenario file under `scenarios/` (preferred for experiments)
- **Anchor (sector) parameters**: default in `inputs.json` → `anchor_params`; override via scenario `overrides.constants`
- **Other/Direct client (material) parameters**: default in `inputs.json` → `other_params`; override via scenario `overrides.constants`
- **Capacity/Price (material lookups)**: default in `inputs.json` → `production`/`pricing`; override via scenario `overrides.points`
- **Primary material map (sector→materials)**: default in `inputs.json` → `primary_map`; override via scenario `overrides.primary_map`
- **Seeding (anchor/direct clients)**: define in the scenario file under `seeds`
- **Lists (Markets/Sectors/Materials)**: default vocabulary in `inputs.json` → `lists`

### Using the Streamlit UI (Scenario Editor)
- Launch with Make (recommended):
  - `make install`
  - `make run_ui` (opens `http://localhost:8501` by default)
- Manual:
  - `python3 -m venv venv && source venv/bin/activate`
  - `python -m pip install -r requirements.txt`
  - `streamlit run ui/app.py` (default port 8501)
- Docker (optional):
  - `docker build -f Dockerfile.ui -t fff-ui .`
  - `docker run --rm -p 8501:8501 -v "$PWD/scenarios:/app/scenarios" -v "$PWD/logs:/app/logs" -v "$PWD/output:/app/output" fff-ui`

What the UI does:
- Edit Runspecs, Constants, Points, Primary Map, and Seeds (tabs)
- Validate in-memory (no disk IO) using backend rules
- Save YAML to `scenarios/`
- Run the model and stream logs; preview KPI CSV
- When "Generate plots" is enabled, plot PNGs are created under `output/plots/` and shown inline with download buttons

Run controls (sidebar):
- **Run Preset**: runs an existing file by name (`--preset <name>`); ignores unsaved editor state.
- **Validate, Save, and Run**: validates the current editor state, writes `scenarios/<name>.yaml` (auto‑suffix if needed), and runs it (`--scenario <path>`).

### Run controls (Scenario runspecs)
- starttime (global): simulation start year (e.g., 2025.0)
- stoptime (global): simulation stop year (exclusive bound)
- dt (global): step size in years (e.g., 0.25 = 1 quarter)

### Static parameters — Anchor (sector-specific)
These drive Anchor Client lead generation, project lifecycle, and post-activation material requirements.
- anchor_start_year: year the sector begins anchor activity
- anchor_client_activation_delay (quarters): wait from threshold to ACTIVE
- anchor_lead_generation_rate (per quarter): base anchor leads rate
- lead_to_pc_conversion_rate (fraction): fraction of leads becoming potential clients
- project_generation_rate (per quarter): per-agent project start rate while POTENTIAL
- max_projects_per_pc (count): cap on projects started while POTENTIAL
- project_duration (quarters): time for a project to complete
- projects_to_client_conversion (count): completed projects needed to schedule activation
- initial_phase_duration (quarters)
- ramp_phase_duration (quarters)
- initial_requirement_rate (per quarter)
- initial_req_growth (per quarter growth)
- ramp_requirement_rate (per quarter)
- ramp_req_growth (per quarter growth)
- steady_requirement_rate (per quarter)
- steady_req_growth (per quarter growth)
- requirement_to_order_lag (quarters): lag from sector requirement to delivery (can be overridden per-(sector, material) in `anchor_params_sm` or via scenario constants)
- ATAM (count): Anchor TAM for gating (paired with CPC stock in SD model)

Each of the above is provided for every sector in `lists.Sector`.

### Static parameters — Direct Clients / “Other” (material-specific)
These drive non-anchor (“other clients”) lead generation, conversion, and order quantities per material.
- lead_start_year: year the material begins receiving other-client leads
- inbound_lead_generation_rate (per quarter)
- outbound_lead_generation_rate (per quarter)
- lead_to_c_conversion_rate (fraction): lead to client conversion
- lead_to_requirement_delay (quarters): lead-to-requirement delay for first requirement
- requirement_to_fulfilment_delay (quarters): requirement-to-delivery delay for running requirements
- avg_order_quantity_initial (units per client)
- client_requirement_growth (per quarter growth)
- TAM (clients): total addressable market for other clients

Each of the above is provided for every material in `lists.Material`.

### Time-series lookups — Material capacity and price (material-specific)
Per-material yearly points, used as dynamic converters during the run.
- Production capacity points: list of {Year, Capacity}. Units are per-year (the model converts to per-quarter internally)
- Pricing points: list of {Year, Price}. Currency is business-defined (consistent across materials)

These are provided per material and can be overridden per scenario.

### Primary material mapping — Sector-to-material assignment
Defines which materials each sector can demand from, with start years controlling when a sector begins using a material.
- For each sector: list of {material, start_year}

The mapping is consumed by both the agent factories and the SD gateway structure.

Notes (Phase 13 multi-material anchors):
- A sector may map to multiple materials. Each entry has an independent `start_year`.
- Scenario overrides can atomically replace a sector’s mapping via `overrides.primary_map[<Sector>]` with a full list of `{material, start_year}` entries.
- Validation requires:
  - Sector and materials exist in `lists`
  - Each material also exists in `other_params`, `production`, and `pricing`
  - `start_year` numeric
- The UI includes a Primary Map editor; proposed replacements are validated with the same rules before saving.
- UI interplay with constants: after you propose new mappings in the Primary Map tab and click "Apply Mapping for Sector", the Constants tab expands its permissible list to include those (sector, material) pairs for overrides. In sector mode, only the targeted per‑(s,m) requirement_* family appears; for the full per‑(s,m) anchor_* set, switch Runspecs → `anchor_mode` to `sm` (strict mode).

### Scenario overrides (optional)
Scenarios can alter defaults without changing `inputs.json`.
- Constants overrides (sector-/material-specific):
  - You can override any anchor (sector-level) or other (material-level) parameter listed above.
  - Business intent: “set this parameter to a new constant value for a given sector/material.”
- Points overrides (material-specific lookups):
  - price_<Material>: replace the material’s price time series with custom [(year, value)] points
  - max_capacity_<Material>: replace the material’s capacity time series with custom [(year, value)] points (specified per-year)
- Primary map overrides:
  - Replace a sector’s material list entirely with a new list of {material, start_year}
  - Applied atomically per sector; unspecified sectors remain unchanged

### Seeding (optional, scenario-level)
Allows initializing the model with pre-existing anchor and direct clients.
- active_anchor_clients (sector-specific): map of sector -> non-negative integer count of ACTIVE anchor clients at t0
- elapsed_quarters (sector-specific): map of sector -> non-negative integer; ages seeded anchor clients by that many quarters
- direct_clients (material-specific): map of material -> non-negative integer count for other (direct) clients at t0

### Lists (global vocabulary)
The following lists define the universe used elsewhere. In the current model only the “US” market is used operationally.
- Markets: e.g., ["US", "EU"]
- Sectors: e.g., ["Defense", "Nuclear", "Semiconductors", "Aviation"]
- Materials: e.g., ["Silicon Carbide Fiber", "Silicon Carbide Powder", "Silicon Nitride Fiber", "UHT", "Boron_fiber", "B4C_Fiber", "WC_Fiber"]

### Units and scaling ()
- Time axis is in years; dt is in years (0.25 = one quarter)
- Quoted “quarters” fields are provided as quarter counts in inputs and used directly as such
- Per-quarter rates (e.g., lead/proj/requirement rates) are interpreted on quarter steps; the SD model and runner handle scaling to dt
- Production capacity points are per-year; the SD model converts to per-quarter internally

### Where to set inputs
- Default values: `inputs.json`
- Scenario-specific changes: scenario YAML files under `scenarios/` via:
  - `runspecs` (start/stop/dt)
  - `overrides.constants`, `overrides.points`, `overrides.primary_map`
  - `seeds.active_anchor_clients`, `seeds.elapsed_quarters`, `seeds.direct_clients`

## How to add a new material (step-by-step)
1) **Choose the exact material name** you’ll use everywhere (case/spaces matter; keep it consistent across all sections).
2) In `inputs.json` → `lists[2].Material`, **append the material name**.
3) In `inputs.json` → `other_params`, **add entries for the new material** under every required key:
   - `lead_start_year`, `inbound_lead_generation_rate`, `outbound_lead_generation_rate`,
     `lead_to_c_conversion_rate`, `lead_to_requirement_delay`, `requirement_to_fulfilment_delay`,
     `avg_order_quantity_initial`, `client_requirement_growth`, `TAM`.
4) In `inputs.json` → `production`, **add yearly capacity points** for the material (per-year units; years strictly increasing; non-negative).
5) In `inputs.json` → `pricing`, **add yearly price points** for the material (years strictly increasing).
6) In `inputs.json` → `primary_map`, **link sectors to the new material** with appropriate `start_year` for any sector that will generate anchor demand for it.
   - If you skip this, anchor agents won’t demand that material; only direct clients will affect it.
7) (Optional) In a scenario file under `scenarios/`, provide **overrides** if you want to experiment with constants or time-series without changing `inputs.json`.
8) (Optional) Seed initial clients in the scenario:
   - `seeds.direct_clients[<Material>]` to seed other (direct) clients
   - If anchor demand is needed immediately, ensure the sector is mapped in `primary_map` and consider `seeds.active_anchor_clients[<Sector>]`.
9) **Run** `python simulate_fff_growth.py --preset <your_scenario>` and review logs/outputs. The loader will validate that all required tables cover the new material and that years are strictly increasing.

## How to add a new sector (step-by-step)
1) In `inputs.json` → `lists[1].Sector`, **append the sector name** (keep exact casing/spaces consistent everywhere).
2) In `inputs.json` → `anchor_params`, **add a value for the new sector under every required anchor key**:
   - `anchor_start_year`, `anchor_client_activation_delay`, `anchor_lead_generation_rate`,
     `lead_to_pc_conversion_rate`, `project_generation_rate`, `max_projects_per_pc`, `project_duration`,
     `projects_to_client_conversion`, `initial_phase_duration`, `ramp_phase_duration`,
     `initial_requirement_rate`, `initial_req_growth`, `ramp_requirement_rate`, `ramp_req_growth`,
     `steady_requirement_rate`, `steady_req_growth`, `requirement_to_order_lag`, `ATAM`.
   - The model only builds sector blocks for sectors present in anchor params; missing any key will be flagged during ingestion/model build.
3) In `inputs.json` → `primary_map`, **map the new sector to one or more materials** with `{material, start_year}` entries.
   - At least one mapping is required for the ABM to generate material requirements; otherwise the factory will error that the sector has no primary materials.
4) (Optional) In a scenario, you can **override** any of the sector’s constants via `overrides.constants`.
5) (Optional) Seed initial anchor clients via scenario `seeds.active_anchor_clients[<Sector>]` and optionally age them via `seeds.elapsed_quarters`.
6) **Run** the model; the loader will validate that the new sector is fully covered in anchor params and that its material mappings refer to known materials.

## How to add or change a sector→material assignment only
- To add another material for an existing sector, edit `inputs.json` → `primary_map[<Sector>]` and **append** `{material, start_year}`.
- Alternatively, in a scenario file you can use `overrides.primary_map[<Sector>]` to **replace** that sector’s entire material list for the run (scenario cannot introduce a brand new sector; sectors must already exist in `lists.Sector`).
- Ensure the material is present in:
  - `lists.Material`
  - `other_params` (all keys for the material)
  - `production` points for the material
  - `pricing` points for the material

## How to set per-(sector, material) Anchor parameters (Phase 16) and enable SM-mode (Phase 17)

You can now specify certain Anchor requirement parameters at the sector–material pair level. This is useful when one sector’s behavior differs across materials.

What can be set per (sector, material):
- initial_requirement_rate, initial_req_growth
- ramp_requirement_rate, ramp_req_growth
- steady_requirement_rate, steady_req_growth
- requirement_to_order_lag

Two ways to provide these values:
1) In `inputs.json` (default):
   - Add an `anchor_params_sm` section with nested maps:
     - Top-level keys are parameter names (from the list above)
     - Second level keys are sectors
     - Third level keys are materials
   - Example (JSON fragment):
     {
       "anchor_params_sm": {
         "requirement_to_order_lag": {
           "Defense": { "Silicon Carbide Fiber": 2.0 }
         },
         "ramp_requirement_rate": {
           "Defense": { "Silicon Carbide Fiber": 300.0 }
         }
       }
     }

2) In a scenario file (override for a single run):
   - Use `overrides.constants` with names in the form `<param>_<Sector>_<Material>` where spaces are replaced by underscores.
   - Example (YAML):
     overrides:
       constants:
         requirement_to_order_lag_Defense_Silicon_Carbide_Fiber: 2.0
         ramp_requirement_rate_Defense_Silicon_Carbide_Fiber: 300.0

Scenario-defined SM coverage (advanced):
- You can define per-(sector, material) constants entirely in a scenario and run without adding them to `inputs.json`.
- Support details:
  - Sector-mode: scenarios may provide the targeted subset only (initial/ramp/steady rates & growth, requirement_to_order_lag) for any (s,m) pair present in `primary_map` (including pairs added via `overrides.primary_map`).
  - SM-mode: scenarios may also provide the full per-(s,m) anchor set. The loader now considers scenario per-(s,m) constants as satisfying SM coverage; missing triples in `inputs.json` no longer block the run if supplied by the scenario.
  - Order-of-operations: the loader validates `overrides.primary_map` first, expands permissible constants to include those pairs (the UI mirrors this so you can select constants immediately), validates constants/points, then merges scenario per‑(s,m) constants into the in‑memory bundle before model build. This guarantees constants exist at build time.
  - Strictness is unchanged: unknown names are errors; names must match canonical `anchor_constant_sm(param, sector, material)`.

Notes:
- SM-mode still requires an explicit `lists_sm` in `inputs.json` when running in strict SM-mode, unless scenarios rely purely on sector-mode (where `lists_sm` is optional). Lists remain the SM universe for validation; `overrides.primary_map` expands permissible pairs for scenario constants.

Universe of (sector, material) pairs (SM list):
- Optionally define `lists_sm` in `inputs.json` as an array of {Sector, Material} rows if you want to constrain which (s,m) pairs are considered.
- If `lists_sm` is absent, the model derives the SM list from `primary_map` automatically.

SM-mode vs Sector-mode:
- Sector-mode (default): targeted per-(s,m) params are optional with precedence below.
- SM-mode (runspecs.anchor_mode: "sm"): strict; all anchor parameters must be present for every pair in `lists_sm`; sector-level fallbacks are disabled. You must also provide `lists_sm` explicitly in `inputs.json`.

Precedence in sector-mode (how values are chosen):
- For each targeted parameter at a specific (sector, material):
  1) Use the per-(s,m) value if provided via `anchor_params_sm` or scenario constant
  2) Else use the sector-level value from `anchor_params`
  3) Else the run fails with a clear validation error

Tips for business users:
- To experiment without editing `inputs.json`, prefer scenario files under `scenarios/` and set per-(s,m) constants in `overrides.constants` using the exact element names shown above.
- Names must match exactly; the loader will show “nearest matches” on typos but will not apply unknown keys.
- After a run, compare `output/FFF_Growth_System_Complete_Results_<scenario>.csv` to the baseline to see the timing (lag), magnitude, and growth-rate impacts.

SM-mode quickstart (Phase 17.7 example scenarios):
- `scenarios/sm_minimal.yaml`: minimal SM run; relies on full `anchor_params_sm` and `lists_sm` in `inputs.json`; seeds one Defense–Silicon Carbide Fiber agent.
- `scenarios/sm_full_demo.yaml`: demonstrates overrides of per-(s,m) constants and seeding multiple pairs.

### Per-(sector, material) parameters: visibility by mode (UI and schema)

The table below summarizes which per-(sector, material) anchor parameters are available to override in Sector mode vs SM mode, and where they appear in the UI. All per‑(s,m) values also map to `inputs.json → anchor_params_sm` for defaults and can be overridden in scenarios via `overrides.constants` using `anchor_constant_sm(param, sector, material)` names.

| Parameter (per‑(s,m)) | Sector mode (anchor_mode = "sector") | SM mode (anchor_mode = "sm") | Notes |
| --- | --- | --- | --- |
| initial_requirement_rate | Constants tab: visible per‑(s,m); override allowed | Constants tab: visible per‑(s,m); override allowed | Targeted requirement family allowed in both modes |
| initial_req_growth | Constants tab: visible per‑(s,m) | Constants tab: visible per‑(s,m) |  |
| ramp_requirement_rate | Constants tab: visible per‑(s,m) | Constants tab: visible per‑(s,m) |  |
| ramp_req_growth | Constants tab: visible per‑(s,m) | Constants tab: visible per‑(s,m) |  |
| steady_requirement_rate | Constants tab: visible per‑(s,m) | Constants tab: visible per‑(s,m) |  |
| steady_req_growth | Constants tab: visible per‑(s,m) | Constants tab: visible per‑(s,m) |  |
| requirement_to_order_lag | Constants tab: visible per‑(s,m) | Constants tab: visible per‑(s,m) | Sector mode precedence falls back to sector‑level lag if per‑(s,m) is absent |
| anchor_start_year | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) | Full per‑(s,m) anchor set enabled only in SM mode |
| anchor_client_activation_delay | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |
| anchor_lead_generation_rate | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |
| lead_to_pc_conversion_rate | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |
| project_generation_rate | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |
| max_projects_per_pc | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |
| project_duration | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |
| projects_to_client_conversion | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |
| initial_phase_duration | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |
| ramp_phase_duration | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |
| ATAM | Not available per‑(s,m); use sector‑level | Constants tab: visible per‑(s,m) |  |

UI behavior notes:
- After you propose new sector→material pairs in the Primary Map tab and click "Apply Mapping for Sector", the Constants tab includes those pairs in its permissible list. In Sector mode you’ll see the targeted requirement_* family and `requirement_to_order_lag` per‑(s,m); in SM mode you’ll see the full per‑(s,m) anchor set as listed above.
- All names shown in the UI correspond 1:1 to the canonical element names used in scenarios (spaces replaced with underscores).


