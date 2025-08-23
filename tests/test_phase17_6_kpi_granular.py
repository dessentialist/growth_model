import os
import unittest
from pathlib import Path

from src.kpi_extractor import build_row_order


class TestPhase176RowOrder(unittest.TestCase):
    def test_build_row_order_defaults_and_granular(self):
        sectors = ["Defense", "Aviation"]
        materials = ["Silicon Carbide Fiber", "Boron_fiber"]
        sector_to_materials = {
            "Defense": ["Silicon Carbide Fiber"],
            "Aviation": ["Boron_fiber"],
        }

        # Default: no granular rows
        rows_default = build_row_order(
            sectors=sectors,
            materials=materials,
            include_sm_revenue_rows=False,
            include_sm_client_rows=False,
            sector_to_materials=sector_to_materials,
        )
        self.assertTrue("Revenue Defense" in rows_default)
        self.assertTrue("Revenue Silicon Carbide Fiber" in rows_default)
        self.assertFalse("Revenue Defense Silicon Carbide Fiber" in rows_default)
        self.assertFalse("Anchor Clients Defense Silicon Carbide Fiber" in rows_default)

        # With granular flags
        rows_gran = build_row_order(
            sectors=sectors,
            materials=materials,
            include_sm_revenue_rows=True,
            include_sm_client_rows=True,
            sector_to_materials=sector_to_materials,
        )
        self.assertTrue("Revenue Defense Silicon Carbide Fiber" in rows_gran)
        self.assertTrue("Anchor Clients Aviation Boron_fiber" in rows_gran)


if __name__ == "__main__":
    unittest.main()


