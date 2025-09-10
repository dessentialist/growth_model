from __future__ import annotations

import streamlit as st

from .base_component import BaseComponent
from ui.services import ExecutionService, ScenarioService
from pathlib import Path


class RunnerTab(BaseComponent):
    """Tab 8: Simulation execution (Phase 4).

    Features:
    - Save current UI state to `scenarios/<name>.yaml`
    - Validate scenario via backend
    - Start/stop run of `simulate_growth.py` with options
    - Show minimal status (PID, scenario, started time)
    - Display tail of `logs/run.log`
    """

    def __init__(self, state, execution_service: ExecutionService):
        super().__init__(state)
        self.execution_service = execution_service
        self.scenario_service = ScenarioService()

    def render(self) -> None:
        st.header("Runner")
        st.caption("Save → Validate → Run. Logs stream below. Use Stop to terminate.")

        # Output file name and actions (use saved scenario from Specs)
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            output_base = st.text_input("Output file name", value=self.state.name, help="Used only for results CSV naming; scenario YAML is chosen from Simulation Specs")
        with col_b:
            if st.button("Validate", key="runner_validate"):
                self._handle_validate(self.state.name)
        with col_c:
            if st.button("Clear Stale Status", key="runner_clear_stale"):
                ok, msg = self.execution_service.clear_stale_status()
                if ok:
                    st.success(msg)
                else:
                    st.info(msg)
        # Show which scenario file will be used for the run
        st.caption(f"Current scenario: {self.state.name}")

        # (Optional) remove after diagnosis; keeping UI lean

        st.divider()

        # Run options (defaults: all enabled except debug)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            debug = st.toggle("Debug logs", value=False, help="Enable verbose runner logging")
        with col2:
            st.caption("Plots: on by default")
            visualize = True
        with col3:
            st.caption("KPI SM revenue rows: on by default")
            kpi_rev = True
        with col4:
            st.caption("KPI SM client rows: on by default")
            kpi_cli = True

        # Start/Stop controls and status
        col5, col6 = st.columns([1, 3])
        with col5:
            if st.button("Start Run", type="primary", key="runner_start"):
                # Use the currently loaded scenario from Simulation Specs
                saved_path = (Path(self.scenario_service.scenarios_dir) / f"{self.state.name}.yaml").resolve()
                if saved_path.exists():
                    # Use output file name independent of scenario
                    output_name = output_base
                    ok, msg = self.execution_service.run_simulation(
                        scenario_path=saved_path,
                        output_name=output_name,
                        debug=debug,
                        visualize=visualize,
                        kpi_sm_revenue_rows=kpi_rev,
                        kpi_sm_client_rows=kpi_cli,
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.error(f"Scenario file not found: {saved_path}. Save it from the Simulation Specs tab first.")
        with col6:
            if st.button("Stop Run", key="runner_stop"):
                ok, msg = self.execution_service.stop_simulation()
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

        # Show status only (logs are in Logs tab)
        status = self.execution_service.get_execution_status()
        st.write({k: v for k, v in status.items() if k != "last_log_lines"})

        # Manual refresh control for status
        st.button("Refresh status", key="runner_refresh")

        # Track running→finished transition to emit an accurate alert (always on)
        if "runner_prev_running" not in st.session_state:
            st.session_state.runner_prev_running = False
        prev_running = bool(st.session_state.runner_prev_running)
        now_running = bool(status.get("running"))
        if prev_running and not now_running:
            st.success("Run complete. Click Generate Preview to view results.")
        st.session_state.runner_prev_running = now_running

        # Light auto-refresh while running to catch completion without manual clicks
        if now_running:
            try:
                from streamlit_autorefresh import st_autorefresh  # type: ignore

                st_autorefresh(interval=2000, key="runner_notify_autorefresh")
            except Exception:
                pass

        st.divider()
        st.info("Results have moved to the Results tab. After a run completes, open the Results tab to preview CSVs and plots.")

    def _handle_validate(self, scenario_name: str) -> None:
        """Strict validation without saving; shows detailed messages."""
        data = self.state.to_scenario_dict_normalized()
        ok, errors = self.scenario_service.validate_scenario(data)
        if ok:
            st.success("Scenario is valid.")
        else:
            st.error("Scenario is invalid.")
            with st.expander("Errors", expanded=True):
                for e in errors:
                    st.write(f"- {e}")


def render_runner_tab(state, execution_service: ExecutionService) -> None:
    RunnerTab(state, execution_service).render()


