import unittest

from src.kpi_extractor import build_row_order


class TestPhase176RowOrder(unittest.TestCase):
    def test_build_row_order_defaults_and_granular(self):
        sectors = ["Sector_One", "Sector_Two"]
        products = ["Product_One", "Product_Two"]
        sector_to_products = {
            "Sector_One": ["Product_One"],
            "Sector_Two": ["Product_Two"],
        }

        # Default: no granular rows
        rows_default = build_row_order(
            sectors=sectors,
            products=products,
            include_sm_revenue_rows=False,
            include_sm_client_rows=False,
            sector_to_products=sector_to_products,
        )
        self.assertTrue("Revenue Sector_One" in rows_default)
        self.assertTrue("Revenue Product_One" in rows_default)
        self.assertFalse("Revenue Sector_One Product_One" in rows_default)
        self.assertFalse("Anchor Clients Sector_One Product_One" in rows_default)

        # With granular flags
        rows_gran = build_row_order(
            sectors=sectors,
            products=products,
            include_sm_revenue_rows=True,
            include_sm_client_rows=True,
            sector_to_products=sector_to_products,
        )
        self.assertTrue("Revenue Sector_One Product_One" in rows_gran)
        self.assertTrue("Anchor Clients Sector_Two Product_Two" in rows_gran)


if __name__ == "__main__":
    unittest.main()
