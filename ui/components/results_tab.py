from __future__ import annotations

import streamlit as st
from pathlib import Path

from .base_component import BaseComponent
from ui.services import ExecutionService


class ResultsTab(BaseComponent):
    """Tab 10: Results preview (CSV and plots)."""

    def __init__(self, state) -> None:
        super().__init__(state)
        self.execution_service = ExecutionService()

    def render(self) -> None:
        st.header("Results")

        # Discover latest CSV
        latest = self.execution_service.get_latest_results_csv()
        if latest is None:
            st.info("No results found in output/. Run a simulation from the Runner tab.")
            return

        st.caption(f"Latest CSV: {latest}")
        # Always display full KPI table
        preview = self.execution_service.read_csv_head(latest, max_rows=0)
        if preview is None:
            st.warning("Failed to read CSV preview.")
        else:
            try:
                import pandas as pd  # local import for display only

                df = pd.DataFrame(preview["rows"], columns=preview["columns"])  # type: ignore[index]
                st.dataframe(df, hide_index=True, use_container_width=True)
            except Exception:
                st.text("\n".join([", ".join(map(str, r)) for r in preview.get("rows", [])]))

        # Plots
        images = self.execution_service.list_plot_images()
        if images:
            st.subheader("Plots")
            cols = st.columns(2)
            for idx, img_path in enumerate(images[:8]):
                with cols[idx % 2]:
                    st.image(str(img_path), caption=str(img_path.name))


def render_results_tab(state) -> None:
    ResultsTab(state).render()


