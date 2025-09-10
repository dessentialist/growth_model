"""
Rebuilt Growth Model UI - Phase 1

Minimal scaffolding with 9 tabs, centralized state, and services.
"""

from pathlib import Path
import sys
import streamlit as st

# Ensure project root is on sys.path to enable src imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui.state import UIState
from ui.services import ScenarioService, ValidationService, ExecutionService
from ui.components.simulation_definitions_tab import render_simulation_definitions_tab
from ui.components.simulation_specs_tab import render_simulation_specs_tab
from ui.components.primary_mapping_tab import render_primary_mapping_tab
from ui.components.seeds_tab import render_seeds_tab
from ui.components.client_revenue_tab import render_client_revenue_tab
from ui.components.direct_market_revenue_tab import render_direct_market_revenue_tab
from ui.components.lookup_points_tab import render_lookup_points_tab
from ui.components.runner_tab import render_runner_tab
from ui.components.logs_tab import render_logs_tab


st.set_page_config(page_title="Growth Model UI", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")


def main() -> None:
    # Initialize state
    if "ui_state" not in st.session_state:
        st.session_state["ui_state"] = UIState()
    state: UIState = st.session_state["ui_state"]

    # Initialize services
    scenario_service = ScenarioService()
    validation_service = ValidationService()
    execution_service = ExecutionService()

    st.title("📈 Growth Model UI")
    st.caption("Scenario Editor & Runner")

    tabs = st.tabs([
        "Simulation Definitions",
        "Simulation Specs",
        "Primary Mapping",
        "Seeds",
        "Client Revenue",
        "Direct Market Revenue",
        "Lookup Points",
        "Runner",
        "Logs",
        "Results",
    ])

    with tabs[0]:
        render_simulation_definitions_tab(state)
    with tabs[1]:
        render_simulation_specs_tab(state, scenario_service, validation_service)
    with tabs[2]:
        render_primary_mapping_tab(state)
    with tabs[3]:
        render_seeds_tab(state, scenario_service, validation_service)
    with tabs[4]:
        render_client_revenue_tab(state, validation_service)
    with tabs[5]:
        render_direct_market_revenue_tab(state, validation_service)
    with tabs[6]:
        render_lookup_points_tab(state, scenario_service, validation_service)
    with tabs[7]:
        render_runner_tab(state, execution_service)
    with tabs[8]:
        render_logs_tab(state)
    with tabs[9]:
        try:
            from ui.components.results_tab import render_results_tab

            render_results_tab(state)
        except Exception:
            st.info("Results tab coming soon.")


if __name__ == "__main__":
    main()


