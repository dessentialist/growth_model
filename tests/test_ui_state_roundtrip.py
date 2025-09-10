from __future__ import annotations

from ui.state import UIState, PrimaryMapEntry


def test_ui_state_roundtrip_primary_map_and_points():
    """Verify that UI state can be serialized to a scenario dict and then
    reloaded into a fresh `UIState` without losing critical fields such as
    runspecs, constants, points, primary map entries, and seeds. This guards
    against silent shape/name drift in editor↔writer flows."""
    state = UIState()
    state.name = "curious-bunny"
    state.runspecs.starttime = 2025.0
    state.runspecs.stoptime = 2026.0
    state.overrides.constants["anchor_lead_generation_rate_Sector_One"] = 0.5
    state.overrides.points["price_Product_One"] = [(2025.0, 10.0), (2025.5, 10.0)]
    state.primary_map.by_sector["Sector_One"] = [PrimaryMapEntry(product="Product_One", start_year=2025.0)]
    state.seeds.active_anchor_clients["Sector_One"] = 1

    scenario_dict = state.to_scenario_dict_normalized()

    # Load into a fresh state and ensure key fields survived the round-trip
    loaded = UIState()
    loaded.load_from_scenario_dict(scenario_dict)
    assert loaded.name == state.name
    assert loaded.runspecs.starttime == state.runspecs.starttime
    assert loaded.overrides.constants["anchor_lead_generation_rate_Sector_One"] == 0.5
    assert "price_Product_One" in loaded.overrides.points
    assert loaded.primary_map.by_sector["Sector_One"][0].product == "Product_One"
    assert loaded.seeds.active_anchor_clients["Sector_One"] == 1
