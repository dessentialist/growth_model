from __future__ import annotations

import streamlit as st

from .base_component import BaseComponent
from ui.services import ExecutionService
from io import StringIO


class LogsTab(BaseComponent):
    """Tab 9: Logs display (Phase 4).

    - Tail `logs/run.log` with level and substring filters
    - Show basic file stats
    - Export visible tail as text download
    - Manual refresh; optional light auto-refresh using st_autorefresh when available
    """

    def __init__(self, state) -> None:
        super().__init__(state)
        self.execution_service = ExecutionService()

    def render(self) -> None:
        st.header("Logs")

        # Config
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        with col1:
            level = st.selectbox("Level", ["", "DEBUG", "INFO", "WARNING", "ERROR"], index=2, key="logs_level")
        with col2:
            view_mode = st.selectbox("View", ["From session start", "Tail"], index=0, key="logs_view_mode")
        with col3:
            contains = st.text_input("Contains", value="", key="logs_contains")
        with col4:
            refresh = st.button("Refresh", key="logs_refresh")

        # Optional auto-refresh if available
        try:
            from streamlit_autorefresh import st_autorefresh  # type: ignore

            # Provide a small opt-in checkbox
            auto = st.checkbox("Auto-refresh every 2s", value=False, key="logs_autorefresh_toggle")
            if auto:
                st_autorefresh(interval=2000, key="logs_autorefresh_tick")
        except Exception:
            pass

        # Stats and guidance
        stats = self.execution_service.log_stats()
        if not stats.get("exists"):
            st.info("No log file yet. Start a run from the Runner tab to generate logs.")
        else:
            st.caption(f"Log path: {stats.get('path', 'logs/run.log')} – size: {int(stats.get('size_bytes', 0))} bytes")

        # Render per view mode
        if view_mode == "From session start":
            lines = self.execution_service.read_log_from_last_session(level=level or None, contains=contains or None)
            label = "logs/run.log (from current UI session start)"
        else:
            # Fallback tail size for readability
            tail_lines = 2000
            lines = self.execution_service.tail_log(max_lines=tail_lines, level=level or None, contains=contains or None)
            label = f"logs/run.log tail (last {tail_lines} lines)"
        text = "\n".join(lines)
        st.text_area(label, value=text, height=500)

        # Export
        st.download_button(
            label="Download shown content",
            data=StringIO(text).getvalue(),
            file_name=("run_session.txt" if view_mode == "From session start" else "run_tail.txt"),
            mime="text/plain",
        )


def render_logs_tab(state) -> None:
    LogsTab(state).render()


