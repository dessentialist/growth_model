import unittest
from pathlib import Path

from src.phase1_data import load_phase1_inputs
from src.scenario_loader import load_and_validate_scenario
from src.fff_growth_model import build_phase4_model
from src.naming import (
    agent_demand_sector_input,
    agent_aggregated_demand,
    total_demand,
    fulfillment_ratio,
    delayed_agent_demand,
    anchor_delivery_flow_sector_material,
    anchor_delivery_flow_material,
    anchor_constant,
)


class TestPhase6Gateways(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_phase1_inputs(Path("Inputs"))
        cls.scenario = load_and_validate_scenario(Path("scenarios/baseline.yaml"), bundle=cls.bundle)

    def test_gateways_and_anchor_deliveries_exist(self):
        result = build_phase4_model(self.bundle, self.scenario.runspecs)
        model = result.model

        # Pick one sector-material pair that exists in Primary Material map
        row = self.bundle.primary_map.long.iloc[0]
        sector = str(row.Sector)
        material = str(row.Material)

        # Expect per-sector input converter
        name_input = agent_demand_sector_input(sector, material)
        self.assertIn(name_input, getattr(model, 'converters', {}))

        # Expect aggregated, total demand and fulfillment ratio per material
        name_agg = agent_aggregated_demand(material)
        name_td = total_demand(material)
        name_fr = fulfillment_ratio(material)
        for n in (name_agg, name_td, name_fr):
            self.assertIn(n, getattr(model, 'converters', {}))

        # Expect delayed agent demand and anchor delivery per sector-material
        name_delayed = delayed_agent_demand(sector, material)
        name_adf_sm = anchor_delivery_flow_sector_material(sector, material)
        for n in (name_delayed, name_adf_sm):
            self.assertIn(n, getattr(model, 'converters', {}))

        # Expect material-level anchor delivery aggregator
        name_adf_m = anchor_delivery_flow_material(material)
        self.assertIn(name_adf_m, getattr(model, 'converters', {}))

        # requirement_to_order_lag constant (sector-level) must exist
        name_rtol = anchor_constant("requirement_to_order_lag", sector)
        self.assertIn(name_rtol, getattr(model, 'constants', {}))

        # Numeric update should be accepted for gateway inputs (no compile-time error)
        model.converters[name_input].equation = 5.0
        # Reassign again to ensure idempotency
        model.converters[name_input].equation = 0.0


if __name__ == "__main__":
    unittest.main()


