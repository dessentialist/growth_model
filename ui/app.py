from __future__ import annotations

"""
Streamlit UI — Scenario Editor (Runspecs/Constants/Points) and Runner.

Scope for Phases 3–5 (UX):
- Tabs to edit runspecs, constants, and time-series (points) with live frontend
  validation constrained to permissible keys queried from backend helpers.
- Sidebar retains preset runner controls; clicking Run executes the CLI runner,
  streams `logs/run.log`, and previews the latest KPI CSV in-app.

Model isolation: All edits are in `ui/` and small non-breaking public helpers in
`src/scenario_loader.py`; no SD/ABM logic is modified by the UI layer.
"""

import time
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

from ui.services.runner import (
    build_runner_command,
    find_latest_results_csv,
    start_simulation_process,
    read_log_tail,
)
from ui.services.builder import (
    list_available_scenarios,
    read_scenario_yaml,
    write_scenario_yaml,
)
from ui.state import UIState
from ui.components.runspecs_form import render_runspecs_form
from ui.components.constants_editor import render_constants_editor
from ui.components.points_editor import render_points_editor
from ui.components.primary_map_editor import render_primary_map_editor
from ui.components.seeds_editor import render_seeds_editor
from ui.services.validation_client import get_bundle, get_permissible_keys, try_validate_scenario_dict

# Ensure project root is on sys.path so imports like `ui.*` and `src.*` work even
# when Streamlit sets the working directory to the `ui/` folder.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

st.set_page_config(page_title="Growth System – Scenario Runner", layout="wide")

st.title("Growth System – Scenario Editor & Runner")


# Lazy-load and cache Phase1 bundle and permissible keys based on mode
@st.cache_resource(show_spinner=False)
def _load_bundle():
    return get_bundle()


bundle = _load_bundle()

if "ui_state" not in st.session_state:
    st.session_state["ui_state"] = UIState()

ui_state: UIState = st.session_state["ui_state"]

tabs = st.tabs(["Runspecs", "Constants", "Points", "Primary Map", "Seeds", "Validate & Save", "Run"])

with tabs[0]:
    updated_runspecs, errs = render_runspecs_form(ui_state.runspecs)
    ui_state.runspecs = updated_runspecs
    if errs:
        for e in errs:
            st.error(e)
    # Show quick context for lists
    st.caption("Sectors and products come from inputs.json and are read-only here.")
    st.write(
        {
            "sectors": bundle.lists.sectors[:8],
            "products": bundle.lists.products[:8],
        }
    )

with tabs[1]:
    # If the user has proposed new sector→product mappings in the Primary Map
    # tab, include those pairs so the permissible constants surface expands to
    # cover per-(sector, product) parameters for the new pairs.
    extra_pairs = []
    if ui_state.primary_map.by_sector:
        for s, entries in ui_state.primary_map.by_sector.items():
            for e in entries:
                extra_pairs.append((str(s), str(e.product)))
        # Deduplicate to keep API calls lean
        extra_pairs = sorted(set(extra_pairs))
    perms = get_permissible_keys(
        bundle,
        anchor_mode=ui_state.runspecs.anchor_mode,
        extra_sm_pairs=extra_pairs or None,
    )
    ui_state.overrides = render_constants_editor(ui_state.overrides, perms.constants)

with tabs[2]:
    perms = get_permissible_keys(bundle, anchor_mode=ui_state.runspecs.anchor_mode)
    ui_state.overrides = render_points_editor(ui_state.overrides, perms.points)

with tabs[3]:
    ui_state.primary_map = render_primary_map_editor(ui_state.primary_map, bundle)

with tabs[4]:
    ui_state.seeds = render_seeds_editor(ui_state.seeds, bundle, ui_state.runspecs.anchor_mode)

with tabs[5]:
    st.header("Validate & Save Scenario")
    scenario_dict = ui_state.to_scenario_dict_normalized()
    ok, err = try_validate_scenario_dict(bundle, scenario_dict)
    if ok:
        st.success("Scenario validates against backend rules.")
    else:
        st.error(f"Validation error: {err}")

    scenario_name = st.text_input("Scenario filename (without extension)", value=ui_state.name)
    dest = Path(f"{scenario_name.strip() or ui_state.name}.yaml")
    overwrite = False
    from src.io_paths import SCENARIOS_DIR

    if (SCENARIOS_DIR / dest).exists():
        st.warning(f"File exists: {SCENARIOS_DIR / dest}")
        overwrite = st.checkbox("Confirm overwrite existing file", value=False)
    save_btn = st.button("Save YAML", type="primary")
    # Preset loader/duplicator
    st.markdown("---")
    st.subheader("Load Existing Scenario")
    files = list_available_scenarios()
    if files:
        sel = st.selectbox("Available scenarios", options=[str(p.name) for p in files])
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Load into Editor"):
                data = read_scenario_yaml(sel)
                ui_state.load_from_scenario_dict(data)
                # Streamlit 1.48+: experimental_rerun is deprecated; use st.rerun()
                st.rerun()
        with c2:
            new_name = st.text_input("Duplicate as (new filename)", value=f"copy_of_{sel.rsplit('.', 1)[0]}")
            if st.button("Duplicate"):
                try:
                    src_data = read_scenario_yaml(sel)
                    path = write_scenario_yaml(src_data, Path(f"{new_name}.yaml"))
                    st.success(f"Duplicated to {path}")
                except Exception as e:
                    st.error(f"Duplicate failed: {e}")
    else:
        st.info("No scenarios found under scenarios/ yet.")
    if save_btn:
        ui_state.name = scenario_name.strip() or ui_state.name
        scenario_dict["name"] = ui_state.name
        try:
            if (SCENARIOS_DIR / dest).exists() and not overwrite:
                st.info("Not saving: overwrite not confirmed.")
            else:
                path = write_scenario_yaml(scenario_dict, dest)
                st.success(f"Wrote scenario to {path}")
        except Exception as e:
            st.error(f"Failed to write YAML: {e}")

with st.sidebar:
    st.header("Run Controls (Preset)")
    preset = st.text_input("Preset name", value="baseline")
    debug = st.checkbox("Debug logs", value=True)
    visualize = st.checkbox("Generate plots", value=False)
    kpi_sm_revenue_rows = st.checkbox("KPI: per-(s,m) revenue rows", value=False)
    kpi_sm_client_rows = st.checkbox("KPI: per-(s,m) anchor client rows", value=False)
    run_btn = st.button("Run Preset", type="primary")
    st.markdown("---")
    st.header("Run Current Scenario")
    run_current = st.button(
        "Validate, Save, and Run", help="Validates current editor scenario, saves to scenarios/, and runs it"
    )

log_container = st.container()
results_container = st.container()


# Helper: run a simulation and render logs in the UI by polling the file tail.
# Simpler than a threaded tail; keeps UI responsive enough for MVP.
def _run_and_render_logs(rc):
    # Prefer simple polling of file tail to avoid threads in Streamlit
    proc = start_simulation_process(rc)
    log_container.empty()
    with log_container:
        st.subheader("Logs")
        log_area = st.empty()
        while proc.poll() is None:
            lines = read_log_tail(500)
            if lines:
                log_area.text("\n".join(lines))
            time.sleep(0.5)
        # Final update
        lines = read_log_tail(1000)
        if lines:
            log_area.text("\n".join(lines))
    return int(proc.returncode or 0)


if run_btn:
    st.session_state["running"] = True
    log_container.empty()
    with log_container:
        st.subheader("Logs")
        log_area = st.empty()
        lines: list[str] = []

    # Build command
    rc = build_runner_command(
        preset=preset.strip() or None,
        debug=debug,
        visualize=visualize,
        kpi_sm_revenue_rows=kpi_sm_revenue_rows,
        kpi_sm_client_rows=kpi_sm_client_rows,
    )

    ret = _run_and_render_logs(rc)

    st.success(f"Run finished with exit code {ret}")

    # Results preview
    csv_path = find_latest_results_csv()
    with results_container:
        st.subheader("KPI CSV Preview")
        if csv_path and Path(csv_path).exists():
            df = pd.read_csv(csv_path)
            st.caption(str(csv_path))
            st.dataframe(df.head(50), use_container_width=True)
            # Quick add: render plots if available
            from src.io_paths import OUTPUT_DIR

            plots_dir = OUTPUT_DIR / "plots"
            pngs = sorted(plots_dir.glob("*.png")) if plots_dir.exists() else []
            if pngs:
                st.markdown("---")
                st.subheader("Generated Plots")
                cols = st.columns(2)
                for i, p in enumerate(pngs):
                    with cols[i % 2]:
                        st.image(str(p), caption=p.name, use_container_width=True)
                        with open(p, "rb") as f:
                            st.download_button(
                                label=f"Download {p.name}",
                                data=f,
                                file_name=p.name,
                                mime="image/png",
                            )
        else:
            st.warning("No results CSV found under output/ yet.")

if run_current:
    # Validate current scenario
    scenario_dict = ui_state.to_scenario_dict_normalized()
    ok, err = try_validate_scenario_dict(bundle, scenario_dict)
    if not ok:
        st.error(f"Validation error: {err}")
    else:
        # Save and run
        ui_state.name = ui_state.name.strip() or "working_scenario"
        # Prevent accidental overwrite by auto-suffixing if file exists
        from src.io_paths import SCENARIOS_DIR

        dest = Path(f"{ui_state.name}.yaml")
        final_dest = dest
        if (SCENARIOS_DIR / dest).exists():
            idx = 1
            while (SCENARIOS_DIR / Path(f"{ui_state.name}_{idx}.yaml")).exists():
                idx += 1
            final_dest = Path(f"{ui_state.name}_{idx}.yaml")
        path = write_scenario_yaml(scenario_dict, final_dest)
        rc = build_runner_command(
            scenario_path=path,
            debug=debug,
            visualize=visualize,
            kpi_sm_revenue_rows=kpi_sm_revenue_rows,
            kpi_sm_client_rows=kpi_sm_client_rows,
        )
        ret = _run_and_render_logs(rc)
        st.success(f"Run finished with exit code {ret}")
        csv_path = find_latest_results_csv()
        with results_container:
            st.subheader("KPI CSV Preview")
            if csv_path and Path(csv_path).exists():
                df = pd.read_csv(csv_path)
                st.caption(str(csv_path))
                st.dataframe(df.head(50), use_container_width=True)
                # Quick add: render plots if available
                from src.io_paths import OUTPUT_DIR

                plots_dir = OUTPUT_DIR / "plots"
                pngs = sorted(plots_dir.glob("*.png")) if plots_dir.exists() else []
                if pngs:
                    st.markdown("---")
                    st.subheader("Generated Plots")
                    cols = st.columns(2)
                    for i, p in enumerate(pngs):
                        with cols[i % 2]:
                            st.image(str(p), caption=p.name, use_container_width=True)
                            with open(p, "rb") as f:
                                st.download_button(
                                    label=f"Download {p.name}",
                                    data=f,
                                    file_name=p.name,
                                    mime="image/png",
                                )
            else:
                st.warning("No results CSV found under output/ yet.")

st.info(
    "Use the tabs to edit runspecs, constants, points, primary map, and seeds. "
    "Validate & Save writes YAML; sidebar can run presets or the current scenario."
)
