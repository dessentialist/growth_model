from __future__ import annotations

"""
Runspecs form component for Streamlit.

This module renders inputs for starttime, stoptime, dt, and anchor_mode and
returns an updated RunspecsState. It performs light, immediate validation to
ensure values are in sensible ranges before the backend validation.
"""

from typing import Tuple
import streamlit as st

from ui.state import RunspecsState


def render_runspecs_form(state: RunspecsState) -> Tuple[RunspecsState, list[str]]:
    """Render the runspecs editor and return (updated_state, inline_errors).

    We run simple checks here: start < stop, dt > 0, anchor_mode in {sector, sm}.
    Backend will re-validate comprehensively on Save/Validate.
    """
    st.subheader("Runspecs")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        start = st.number_input("Start Time (year)", value=float(state.starttime), step=0.25, format="%.2f")
    with c2:
        stop = st.number_input("Stop Time (year)", value=float(state.stoptime), step=0.25, format="%.2f")
    with c3:
        dt = st.number_input("dt (years)", value=float(state.dt), step=0.25, format="%.2f", min_value=0.01)
    with c4:
        mode = st.selectbox("Anchor Mode", options=["sector", "sm"], index=(0 if state.anchor_mode == "sector" else 1))

    errors: list[str] = []
    if dt <= 0:
        errors.append("dt must be positive")
    if start >= stop:
        errors.append("starttime must be less than stoptime")
    if mode not in {"sector", "sm"}:
        errors.append("anchor_mode must be 'sector' or 'sm'")

    updated = RunspecsState(starttime=float(start), stoptime=float(stop), dt=float(dt), anchor_mode=str(mode))
    return updated, errors


__all__ = ["render_runspecs_form"]


