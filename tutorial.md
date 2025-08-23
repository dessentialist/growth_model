## FFF Growth System – Business User Tutorial

Audience: Business stakeholders who want to install the tool, use the UI to build scenarios, run the model, and read outputs/plots. No coding required.

### 1) What you’ll get
- A browser UI to edit scenarios (time horizon, constants, time‑series, sector→material mappings, seeding) and run the model
- Live logs, a KPI CSV preview, and downloadable static plots
- Preset scenarios you can run as-is or load into the editor to tweak

### 2) Quick install from GitHub

Prerequisites:
- macOS or Windows/Linux
- Python 3.12+ and Git

Clone and set up a virtual environment (recommended):
```bash
git clone https://github.com/dessentialist/FFF_Growth_System_v2.git
cd FFF_Growth_System_v2

python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
python -m pip install -r requirements.txt
```

Launch the UI:
```bash
streamlit run ui/app.py
```
By default your browser opens at http://localhost:8501

Optional – Makefile helpers (if you use make):
```bash
make install   # create venv + install deps
make run_ui    # open the UI at http://localhost:8501
```

Optional – Docker (no Python needed):
```bash
docker build -f Dockerfile.ui -t fff-ui .
docker run --rm -p 8501:8501 \
  -v "$PWD/scenarios:/app/scenarios" \
  -v "$PWD/logs:/app/logs" \
  -v "$PWD/output:/app/output" \
  fff-ui
```

### 3) UI layout (what each tab does)
The UI has six main areas: Runspecs, Constants, Points, Primary Map, Seeds, Validate & Save, plus run controls in the sidebar.

- Runspecs: choose start year, stop year, dt (step size), and Anchor Mode (sector or sm)
- Constants: override numeric parameters (see section 4)
- Points: override time series for price and capacity per material
- Primary Map: replace a sector’s materials with a new list and start years
- Seeds: seed pre-existing anchor/direct clients at t0
- Validate & Save: validate your in‑memory scenario and save it to `scenarios/`
- Sidebar Run Controls: run a preset by name or validate→save→run your current editor scenario; toggle debug & plots

Tip: The UI only lists “permissible” names that the backend guarantees are valid—filter boxes never let you type a wrong name.

### 4) Constants – which names appear and when
You will see three kinds of constants:
- Per‑sector (e.g., `anchor_lead_generation_rate_Defense`)
- Per‑material (e.g., `lead_start_year_Silicon_Carbide_Fiber`)
- Per‑(sector, material) targeted requirement family (both modes) and full per‑pair anchor set (SM mode only)

Mode details (short version):
- Sector mode (default): you can set per‑(s,m) requirement_* rates/growth and `requirement_to_order_lag` for any sector→material pair; the rest of the anchor parameters remain sector‑level.
- SM mode: you can set the full per‑(s,m) anchor set (e.g., `anchor_start_year_Defense_UHT`, `project_duration_Defense_UHT`, etc.). SM mode is stricter and expects comprehensive per‑(s,m) coverage.

Primary Map interplay:
- In Primary Map, pick a sector, select materials and start years, then click “Apply Mapping for Sector”.
- After that, the Constants tab immediately includes those new (sector, material) pairs in its permissible list so you can add per‑pair overrides.

### 5) Points (time‑series)
- Lookups per material: `price_<Material>` and `max_capacity_<Material>`
- Add rows as [Year, Value], keep years strictly increasing; the UI warns if out of order
- You can remove an override entirely with the “Apply Series” button after clearing rows

### 6) Primary Map (sector→materials)
- Select sector, see its current mapping (read‑only)
- Choose proposed materials and assign `StartYear` per material
- Click “Apply Mapping for Sector” to stage the replacement; it appears in the summary
- This is an atomic replace per sector on save: you provide the full new list for that sector

### 7) Seeds (optional)
- Sector mode:
  - `active_anchor_clients` and optional `elapsed_quarters` per sector
  - `completed_projects` per sector to pre-load a backlog of completed projects at t0. The model converts this deterministically: `floor(completed / projects_to_client_conversion)` ACTIVE anchors at t0; the remainder is discarded.
- SM mode:
  - `active_anchor_clients_sm` per (sector, material)
  - `completed_projects_sm` per (sector, material) to pre-load backlog. Same conversion applies pair-wise (remainder discarded). Optionally use `elapsed_quarters_sm` to age ACTIVE seeds.
- Direct clients: set `direct_clients` per material

### 8) Validate & Save
- Click “Validate & Save Scenario” to run the full backend checks on your in‑memory edits
- Name the scenario and save to `scenarios/<name>.yaml` (UI warns on overwrite; the Run Current flow auto‑suffixes)

### 9) Running scenarios (two ways)
- Sidebar → Run Preset: type a name (e.g., `baseline`) and click Run Preset
  - This runs an existing file in `scenarios/` by name and ignores unsaved editor changes
- Sidebar → Validate, Save, and Run:
  - Validates your current editor state, writes it to `scenarios/<name>.yaml`, then runs it
  - Safe save: if the filename already exists, the UI auto‑suffixes (e.g., `working_scenario_2.yaml`)

Run toggles:
- Debug logs: more detailed logs in `logs/run.log`
- Generate plots: produce PNGs under `output/plots/` and render them in the UI
- KPI extras (advanced): include granular per‑(s,m) KPI rows

### 10) Outputs & where to find them
- Logs: `logs/run.log` (also streamed in UI)
- KPI CSV: `output/FFF_Growth_System_Complete_Results.csv`
- Scenario‑suffixed copy: `output/FFF_Growth_System_Complete_Results_<scenario>.csv`
- Plots: `output/plots/*.png` (rendered inline and downloadable when “Generate plots” is enabled)

### 11) Typical workflows

Workflow A – Quick baseline verification
1) Open UI → Sidebar → Run Preset: `baseline` → Run
2) Review logs, CSV preview, and plots

Workflow B – Change time horizon and run
1) Runspecs: starttime/stoptime/dt
2) Validate & Save → name the scenario
3) Validate, Save, and Run → enable Generate plots

Workflow C – Add a new sector→material and tune per‑pair constants
1) Primary Map: sector = Defense → add `UHT` with StartYear
2) Click “Apply Mapping for Sector”
3) Constants:
   - Sector mode: edit per‑(s,m) requirement_* and `requirement_to_order_lag`
   - SM mode: switch anchor_mode to `sm` to access full per‑(s,m) anchor set
4) Validate & Save → Run with plots

Workflow D – Change a material’s price or capacity shape
1) Points: select `price_<Material>` or `max_capacity_<Material>`
2) Add rows (years strictly increasing)
3) Apply Series → Validate & Save → Run

### 12) Command‑line (optional, without the UI)
Run a preset:
```bash
python simulate_fff_growth.py --preset baseline --debug --visualize
```
Run a specific scenario file:
```bash
python simulate_fff_growth.py --scenario scenarios/your_case.yaml --visualize
```
Flags:
- `--kpi-sm-revenue-rows` and `--kpi-sm-client-rows` append optional per‑(s,m) rows to the CSV

### 13) Troubleshooting
- I don’t see my per‑(s,m) constants after adding a new mapping
  - In Primary Map, click “Apply Mapping for Sector” first
  - In Sector mode you’ll see the requirement_* family and the per‑pair lag; switch to SM mode to see the full per‑pair anchor set

- Validation error about lists_sm in SM mode
  - SM mode is strict and requires an explicit `lists_sm` in `inputs.json` (or provide per‑pair constants comprehensively via the scenario as described in the docs)

- Lookup extrapolation warnings near the horizon
  - Extend your price/capacity points so they cover your stop year; warnings are informational (hold‑last policy) but you can eliminate them with more points

- Overwrites when saving
  - The “Validate, Save, and Run” path auto‑suffixes filenames; the “Validate & Save” tab prompts before overwrite

- Nothing shows under Plots in the UI
  - Check “Generate plots” in the sidebar before running; PNGs appear under `output/plots/`

### 14) Reference materials
- Inputs and naming rules: `inputs.md` (includes a per‑(sector, material) table by mode)
- Technical architecture and flow: `technical_architecture.md` (includes a compact reference table and data‑flow diagrams)
- Example scenarios: `scenarios/` (e.g., `baseline.yaml`, `pm_override_example.yaml`, SM demos)

### 15) Safe changes checklist
- Scenario changes live under `scenarios/` – version them in Git if needed
- Always validate before saving/running; the UI mirrors backend rules
- Prefer SM mode only when you intend full per‑(s,m) control; sector mode is simpler for targeted rate/lag experiments

You’re ready to go. If you want a 60‑second demo call‑out in the UI (tooltips or a side panel), let us know—we can add it next.


