from __future__ import annotations

import streamlit as st

from .base_component import BaseComponent
from ui.services import ScenarioService, ValidationService


class SeedsTab(BaseComponent):
    """Tab 4: Seeds configuration (Phase 3).

    Provides sector-mode and SM-mode seeding plus direct client seeding.
    Writes into `state.seeds` which `UIState.to_scenario_dict[_normalized]`
    includes as the scenario `seeds` block.
    """

    def __init__(self, state, scenario_service: ScenarioService, validation_service: ValidationService) -> None:
        super().__init__(state)
        self.scenario_service = scenario_service
        self.validation_service = validation_service

    def render(self) -> None:
        st.header("Seeds")

        lists = self.scenario_service.get_lists_summary()
        sectors: list[str] = lists.get("sectors", [])
        products: list[str] = lists.get("products", [])

        is_sm = (getattr(self.state.runspecs, 'anchor_mode', 'sector') == 'sm')
        if is_sm:
            st.info("SM mode: Configure seeds per (sector, product). Sector-level seeds are disabled.")
        else:
            st.info("Sector mode: Configure seeds per sector. Per-(s,p) seeds hidden.")

        st.subheader("Anchor Seeds")
        # Per-section reset counters
        if "seeds_reset_count" not in st.session_state:
            st.session_state["seeds_reset_count"] = 0
        # Reset button: restores from last-saved seeds snapshot and rotates keys
        if st.button("Reset to default (Seeds)", key=f"seeds_reset_btn_{st.session_state['seeds_reset_count']}"):
            ls = getattr(self.state, 'last_saved_seeds', {}) or {}
            # Restore sector-mode
            self.state.seeds.active_anchor_clients = dict(ls.get("active_anchor_clients", {}))
            self.state.seeds.elapsed_quarters = dict(ls.get("elapsed_quarters", {}))
            self.state.seeds.completed_projects = dict(ls.get("completed_projects", {}))
            # Restore SM-mode
            self.state.seeds.active_anchor_clients_sm = {s: dict(m) for s, m in ls.get("active_anchor_clients_sm", {}).items()}
            self.state.seeds.elapsed_quarters_sm = {s: dict(m) for s, m in ls.get("elapsed_quarters_sm", {}).items()}
            self.state.seeds.completed_projects_sm = {s: dict(m) for s, m in ls.get("completed_projects_sm", {}).items()}
            # Restore direct clients
            self.state.seeds.direct_clients = dict(ls.get("direct_clients", {}))
            st.session_state["seeds_reset_count"] = int(st.session_state["seeds_reset_count"]) + 1
            st.caption("Reset (Seeds): values restored from last-saved scenario")
        if not is_sm:
            # Sector-mode seeds
            for s in sectors:
                cols = st.columns(3)
                with cols[0]:
                    aac = st.number_input(f"Active anchors at t0 — {s}", min_value=0, value=int(self.state.seeds.active_anchor_clients.get(s, 0)), step=1, key=f"seeds_aac_{s}_{st.session_state['seeds_reset_count']}")
                with cols[1]:
                    eq = st.number_input(f"Elapsed quarters — {s}", min_value=0, value=int(self.state.seeds.elapsed_quarters.get(s, 0)), step=1, key=f"seeds_eq_{s}_{st.session_state['seeds_reset_count']}")
                with cols[2]:
                    cp = st.number_input(f"Completed projects backlog — {s}", min_value=0, value=int(self.state.seeds.completed_projects.get(s, 0)), step=1, key=f"seeds_cp_{s}_{st.session_state['seeds_reset_count']}")
                # Persist only non-zero to keep YAML tidy
                if aac > 0:
                    self.state.seeds.active_anchor_clients[s] = int(aac)
                else:
                    self.state.seeds.active_anchor_clients.pop(s, None)
                if eq > 0:
                    self.state.seeds.elapsed_quarters[s] = int(eq)
                else:
                    self.state.seeds.elapsed_quarters.pop(s, None)
                if cp > 0:
                    self.state.seeds.completed_projects[s] = int(cp)
                else:
                    self.state.seeds.completed_projects.pop(s, None)
        else:
            # SM-mode seeds per (sector, product) limited by current mapping
            st.caption("Pairs available are derived from Primary Mapping.")
            pairs = []
            for sector, entries in self.state.primary_map.by_sector.items():
                for e in entries:
                    pairs.append((sector, e.product))
            if not pairs:
                st.warning("No sector–product pairs mapped. Configure Primary Mapping first.")
            for (s, p) in pairs:
                cols = st.columns(3)
                current_sm_aac = int(self.state.seeds.active_anchor_clients_sm.get(s, {}).get(p, 0))
                current_sm_eq = int(self.state.seeds.elapsed_quarters_sm.get(s, {}).get(p, 0))
                current_sm_cp = int(self.state.seeds.completed_projects_sm.get(s, {}).get(p, 0))
                with cols[0]:
                    aac = st.number_input(f"ACTIVE at t0 — {s} / {p}", min_value=0, value=current_sm_aac, step=1, key=f"seeds_sm_aac_{s}_{p}_{st.session_state['seeds_reset_count']}")
                with cols[1]:
                    eq = st.number_input(f"Elapsed qtrs — {s} / {p}", min_value=0, value=current_sm_eq, step=1, key=f"seeds_sm_eq_{s}_{p}_{st.session_state['seeds_reset_count']}")
                with cols[2]:
                    cp = st.number_input(f"Completed proj backlog — {s} / {p}", min_value=0, value=current_sm_cp, step=1, key=f"seeds_sm_cp_{s}_{p}_{st.session_state['seeds_reset_count']}")

                if aac > 0:
                    self.state.seeds.active_anchor_clients_sm.setdefault(s, {})[p] = int(aac)
                else:
                    if s in self.state.seeds.active_anchor_clients_sm:
                        self.state.seeds.active_anchor_clients_sm[s].pop(p, None)
                        if not self.state.seeds.active_anchor_clients_sm[s]:
                            self.state.seeds.active_anchor_clients_sm.pop(s, None)
                if eq > 0:
                    self.state.seeds.elapsed_quarters_sm.setdefault(s, {})[p] = int(eq)
                else:
                    if s in self.state.seeds.elapsed_quarters_sm:
                        self.state.seeds.elapsed_quarters_sm[s].pop(p, None)
                        if not self.state.seeds.elapsed_quarters_sm[s]:
                            self.state.seeds.elapsed_quarters_sm.pop(s, None)
                if cp > 0:
                    self.state.seeds.completed_projects_sm.setdefault(s, {})[p] = int(cp)
                else:
                    if s in self.state.seeds.completed_projects_sm:
                        self.state.seeds.completed_projects_sm[s].pop(p, None)
                        if not self.state.seeds.completed_projects_sm[s]:
                            self.state.seeds.completed_projects_sm.pop(s, None)

        st.subheader("Direct Clients Seeds (per product)")
        for p in products:
            val = st.number_input(f"Direct clients at t0 — {p}", min_value=0, value=int(self.state.seeds.direct_clients.get(p, 0)), step=1, key=f"seeds_dc_{p}_{st.session_state['seeds_reset_count']}")
            if val > 0:
                self.state.seeds.direct_clients[p] = int(val)
            else:
                self.state.seeds.direct_clients.pop(p, None)


def render_seeds_tab(state, scenario_service: ScenarioService, validation_service: ValidationService) -> None:
    SeedsTab(state, scenario_service, validation_service).render()


