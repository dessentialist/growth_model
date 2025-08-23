from __future__ import annotations

"""
Seeds editor component for Streamlit.

This editor collects scenario seeding options for anchors (sector-level and SM-mode)
and direct clients. It mirrors the scenario schema and applies lightweight UI
validation (non-negative integers). Full validation is enforced by the backend.
"""

from typing import Dict
import streamlit as st

from src.phase1_data import Phase1Bundle
from ui.state import SeedsState


def _non_negative_int_input(label: str, value: int, key: str) -> int:
    """Streamlit helper enforcing non-negative integer entry via number_input."""
    v = st.number_input(label, value=int(value), step=1, min_value=0, key=key)
    return int(v)


def render_seeds_editor(state: SeedsState, bundle: Phase1Bundle, anchor_mode: str) -> SeedsState:
    """Render seeds editor and return updated `SeedsState`.

    Tabs:
      - Anchor (sector) — hidden in SM-mode to avoid confusion
      - Anchor SM (sector, material) — visible only in SM-mode
      - Direct clients (per material)
    """
    st.subheader("Seeds")
    st.caption(
        "Tip: Completed projects convert to floor(completed / projects_to_client_conversion) "
        "ACTIVE anchors at t0; the remainder is discarded (per-agent progress is not fungible)."
    )
    sectors = list(map(str, bundle.lists.sectors))
    materials = list(map(str, bundle.lists.materials))

    tabs = []
    tab_labels = []
    if anchor_mode != "sm":
        tab_labels.append("Anchor (sector)")
    if anchor_mode == "sm":
        tab_labels.append("Anchor SM")
    tab_labels.append("Direct clients")
    tabs = st.tabs(tab_labels)

    tab_idx = 0
    if anchor_mode != "sm":
        with tabs[tab_idx]:
            st.caption("Sector-level seeds: ACTIVE anchors at t0, elapsed quarters, and completed projects backlog")
            for s in sectors:
                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    cur = state.active_anchor_clients.get(s, 0)
                    state.active_anchor_clients[s] = _non_negative_int_input(
                        f"ACTIVE anchors @ t0 — {s}", cur, key=f"seed_aac_{s}"
                    )
                with c2:
                    curq = state.elapsed_quarters.get(s, 0)
                    state.elapsed_quarters[s] = _non_negative_int_input(f"Elapsed quarters — {s}", curq, key=f"seed_eq_{s}")
                with c3:
                    curc = state.completed_projects.get(s, 0)
                    state.completed_projects[s] = _non_negative_int_input(
                        f"Completed projects — {s}", curc, key=f"seed_cp_{s}"
                    )
        tab_idx += 1

    if anchor_mode == "sm":
        with tabs[tab_idx]:
            st.caption("SM-mode seeds: ACTIVE anchors and completed projects per (sector, material)")
            for s in sectors:
                st.markdown(f"##### {s}")
                # Active anchors per pair
                row_active: Dict[str, int] = dict(state.active_anchor_clients_sm.get(s, {}))
                # Completed projects per pair
                row_cp: Dict[str, int] = dict(state.completed_projects_sm.get(s, {}))
                for m in materials:
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        cur_a = int(row_active.get(m, 0))
                        row_active[m] = _non_negative_int_input(
                            f"ACTIVE @ t0 — {s} • {m}", cur_a, key=f"seed_sm_active_{s}_{m}"
                        )
                    with c2:
                        cur_c = int(row_cp.get(m, 0))
                        row_cp[m] = _non_negative_int_input(
                            f"Completed projects — {s} • {m}", cur_c, key=f"seed_sm_cp_{s}_{m}"
                        )
                # Persist non-zero entries only
                row_active = {m: v for m, v in row_active.items() if v > 0}
                row_cp = {m: v for m, v in row_cp.items() if v > 0}
                if row_active:
                    state.active_anchor_clients_sm[s] = row_active
                else:
                    state.active_anchor_clients_sm.pop(s, None)
                if row_cp:
                    state.completed_projects_sm[s] = row_cp
                else:
                    state.completed_projects_sm.pop(s, None)
        tab_idx += 1

    with tabs[tab_idx]:
        st.caption("Direct clients @ t0 per material")
        for m in materials:
            cur = state.direct_clients.get(m, 0)
            state.direct_clients[m] = _non_negative_int_input(f"Direct clients — {m}", cur, key=f"seed_dc_{m}")

    # Cleanup zero entries to avoid noisy YAML
    state.active_anchor_clients = {k: v for k, v in state.active_anchor_clients.items() if v > 0}
    state.elapsed_quarters = {k: v for k, v in state.elapsed_quarters.items() if v > 0}
    state.direct_clients = {k: v for k, v in state.direct_clients.items() if v > 0}
    state.completed_projects = {k: v for k, v in state.completed_projects.items() if v > 0}

    return state


__all__ = ["render_seeds_editor"]
