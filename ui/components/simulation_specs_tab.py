from __future__ import annotations

import streamlit as st

from .base_component import BaseComponent
from ui.services import ScenarioService, ValidationService


class SimulationSpecsTab(BaseComponent):
    """Tab 2: Runtime controls & basic scenario management (Phase 1).

    Implements minimal, reliable controls for start/stop/dt and anchor_mode,
    plus load/save against the scenarios directory via ScenarioService.
    """

    def __init__(self, state, scenario_service: ScenarioService, validation_service: ValidationService):
        super().__init__(state)
        self.scenario_service = scenario_service
        self.validation_service = validation_service

    def render(self) -> None:
        st.header("Simulation Specs")
        st.caption("Core runtime controls and scenario load/save.")

        # Bootstrap last selection on first render to persist across refreshes
        if not st.session_state.get("specs_bootstrap_done", False):
            try:
                last = self.scenario_service.get_last_selected()
                last_name = (last.get("name") or "").strip()
                if last_name:
                    raw = self.scenario_service.load_scenario(last_name)
                    bundle = self.scenario_service.get_inputs_bundle()
                    self.state.load_from_scenario_dict(raw, bundle=bundle)
                    # Snapshot last-saved from YAML for Reset buttons across tabs
                    if hasattr(self.state, 'snapshot_as_last_saved'):
                        self.state.snapshot_as_last_saved()
                    if hasattr(self.state, 'name'):
                        self.state.name = last_name
                    else:
                        self.state.current_scenario = last_name
                    st.session_state["specs_current_scenario"] = last_name
                    st.session_state["specs_anchor_mode"] = (getattr(self.state.runspecs, 'anchor_mode', 'sector') == 'sm')
            except Exception:
                pass
            st.session_state["specs_bootstrap_done"] = True
            st.rerun()

        # Runtime controls
        with st.expander("Runtime Controls", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                starttime = st.number_input("Start Year", value=float(self.state.runspecs.starttime), step=1.0)
            with col2:
                stoptime = st.number_input("Stop Year", value=float(self.state.runspecs.stoptime), step=1.0)
            with col3:
                dt = st.number_input("dt (years)", value=float(self.state.runspecs.dt), step=0.25, format="%.2f")

            ok, errors = self.validation_service.validate_runtime(starttime, stoptime, dt)
            if ok:
                self.state.runspecs.starttime = float(starttime)
                self.state.runspecs.stoptime = float(stoptime)
                self.state.runspecs.dt = float(dt)
            else:
                for e in errors:
                    st.error(e)

            # Anchor mode as a toggle: OFF = sector, ON = sm
            current_is_sm = (getattr(self.state.runspecs, 'anchor_mode', 'sector') == 'sm')
            new_is_sm = st.toggle("SM mode", value=current_is_sm, help="Toggle between sector mode (off) and SM mode (on)", key="specs_sm_toggle")
            self.state.runspecs.anchor_mode = "sm" if new_is_sm else "sector"

            # Quick assistance: show permissible override key counts for current mode
            with st.expander("Permissible Override Keys (reference)", expanded=False):
                try:
                    names = self.scenario_service.get_permissible_override_keys(anchor_mode=self.state.runspecs.anchor_mode)
                    st.write(f"Constants: {len(names.get('constants', []))} | Points: {len(names.get('points', []))}")
                except Exception as exc:
                    st.warning(f"Unable to fetch permissible keys: {exc}")

        # Scenario management
        with st.expander("Scenario Management", expanded=True):
            scenarios = self.scenario_service.list_scenarios()

            # Current scenario status
            state_current = getattr(self.state, 'name', None) or getattr(self.state, 'current_scenario', "")
            current_name = st.session_state.get("specs_current_scenario", state_current)
            st.write(f"Current scenario: :blue[{current_name or '(unsaved)'}]")

            # Load existing scenario
            st.subheader("Load existing")
            selected = st.selectbox(
                "Available scenarios (to load)",
                options=[""] + scenarios,
                index=(1 + scenarios.index(current_name)) if current_name in scenarios else 0,
                help="Choose an existing scenario and click 'Load Selected Scenario'",
                key="specs_select_scenario",
            )
            if st.button("Load Selected Scenario", use_container_width=True, disabled=(not selected)):
                try:
                    raw = self.scenario_service.load_scenario(selected)
                    # Hydrate from scenario using current inputs bundle so primary_map defaults are loaded
                    bundle = self.scenario_service.get_inputs_bundle()
                    self.state.load_from_scenario_dict(raw, bundle=bundle)
                    # After loading, snapshot as last-saved for Reset behavior across tabs
                    if hasattr(self.state, 'snapshot_as_last_saved'):
                        self.state.snapshot_as_last_saved()
                    if hasattr(self.state, 'name'):
                        self.state.name = selected
                    else:
                        self.state.current_scenario = selected
                    # Persist selection and mode
                    st.session_state["specs_current_scenario"] = selected
                    st.session_state["specs_anchor_mode"] = (getattr(self.state.runspecs, 'anchor_mode', 'sector') == 'sm')
                    try:
                        self.scenario_service.set_last_selected(selected, getattr(self.state.runspecs, 'anchor_mode', 'sector'))
                    except Exception:
                        pass
                    st.success(f"Loaded scenario '{selected}'")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to load: {exc}")

            # Overwrite current scenario (save in place)
            overwrite_label = f"Save (Overwrite current: {current_name})" if current_name else "Save (Overwrite current)"
            if st.button(overwrite_label, use_container_width=True, disabled=(len((current_name or '').strip()) == 0)):
                try:
                    data = self.state.to_scenario_dict_normalized() if hasattr(self.state, 'to_scenario_dict_normalized') else dict(self.state.scenario_data)
                    saved_path = self.scenario_service.save_scenario(data, (current_name or '').strip())
                    # Snapshot current in-memory overrides as last-saved
                    if hasattr(self.state, 'snapshot_as_last_saved'):
                        self.state.snapshot_as_last_saved()
                    try:
                        self.scenario_service.set_last_selected((current_name or '').strip(), getattr(self.state.runspecs, 'anchor_mode', 'sector'))
                    except Exception:
                        pass
                    st.success(f"Saved to {saved_path}")
                except Exception as exc:
                    st.error(f"Failed to save: {exc}")

            st.divider()

            # Save options
            st.subheader("Save options")
            new_name = st.text_input("New scenario name", value="", placeholder="e.g., working_scenario_v2", key="specs_new_name")
            save_new_disabled = len(new_name.strip()) == 0
            if st.button("Save as New", type="primary", use_container_width=True, disabled=save_new_disabled):
                if new_name.strip() in scenarios:
                    st.error("Name already exists. Use 'Overwrite current' to replace an existing scenario.")
                else:
                    try:
                        data = self.state.to_scenario_dict_normalized() if hasattr(self.state, 'to_scenario_dict_normalized') else dict(self.state.scenario_data)
                        saved_path = self.scenario_service.save_scenario(data, new_name.strip())
                        if hasattr(self.state, 'snapshot_as_last_saved'):
                            self.state.snapshot_as_last_saved()
                        if hasattr(self.state, 'name'):
                            self.state.name = new_name.strip()
                        else:
                            self.state.current_scenario = new_name.strip()
                        try:
                            self.scenario_service.set_last_selected(new_name.strip(), getattr(self.state.runspecs, 'anchor_mode', 'sector'))
                        except Exception:
                            pass
                        st.session_state["specs_current_scenario"] = new_name.strip()
                        st.session_state["specs_anchor_mode"] = (getattr(self.state.runspecs, 'anchor_mode', 'sector') == 'sm')
                        st.success(f"Saved new scenario to {saved_path}")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to save new scenario: {exc}")

            st.subheader("Validate Current Scenario")
            if st.button("Validate using backend rules", use_container_width=True):
                try:
                    data = self.state.to_scenario_dict_normalized() if hasattr(self.state, 'to_scenario_dict_normalized') else dict(self.state.scenario_data)
                    # Lenient SM validation: treat orphan per-(s,p) constants as informational only
                    ok, errors = self.scenario_service.validate_scenario(data)
                    if not ok and getattr(self.state.runspecs, 'anchor_mode', 'sector') == 'sm':
                        ok2, errors2, orphans = self.scenario_service.validate_scenario_lenient_sm(data)
                        ok = ok2
                        errors = errors2
                        if orphans:
                            st.warning(f"Orphan SM constants ignored for validation: {len(orphans)} (e.g., {orphans[:3]})")
                    if ok:
                        st.success("Scenario is valid against current inputs.json")
                    else:
                        for e in errors:
                            st.error(e)
                except Exception as exc:
                    st.error(f"Validation failed: {exc}")


def render_simulation_specs_tab(state, scenario_service: ScenarioService, validation_service: ValidationService) -> None:
    SimulationSpecsTab(state, scenario_service, validation_service).render()


