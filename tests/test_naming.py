import unittest

# Tests for Phase 2 naming utilities. These are intentionally simple and
# deterministic to validate normalization, truncation, helper alignment, and
# registry collision detection behavior as specified in the architecture.
from src.naming import (
    NameRegistry,
    create_element_name,
    anchor_constant,
    product_constant,
    price_lookup_name_product,
    anchor_lead_generation,
)


class TestNamingUtilities(unittest.TestCase):
    def test_basic_normalization(self):
        # Verifies that spaces and punctuation collapse to single underscores
        # and that case is preserved to match canonical names.
        name = create_element_name("Anchor Lead Generation", "Sector One & Two")
        self.assertEqual(name, "Anchor_Lead_Generation_Sector_One_Two")

    def test_material_component(self):
        # Verifies that material-only components are appended in third position
        # and formatted with underscores.
        name = create_element_name("Price", material="Product One")
        self.assertEqual(name, "Price_Product_One")

    def test_collision_safe_truncation(self):
        # Builds a very long sector to trigger truncation and ensures the
        # truncated result is stable (same inputs -> same output) and bounded
        # by the default 100-char limit.
        long_sector = "Very Long Sector Name With Many Characters !@# $% ^&*()" * 3
        n1 = create_element_name("Anchor_Lead_Generation", long_sector)
        n2 = create_element_name("Anchor_Lead_Generation", long_sector)
        self.assertEqual(n1, n2)  # stable hash and truncation
        self.assertLessEqual(len(n1), 100)

    def test_registry_detects_conflict(self):
        # Confirms the registry tracks final names -> source tuples and raises
        # on conflicting re-registrations with different sources.
        reg = NameRegistry()
        n = create_element_name("X", "A", "B", registry=reg)
        # same mapping is fine
        create_element_name("X", "A", "B", registry=reg)
        self.assertTrue(n)
        # Force a conflict by direct register call with a different source triple
        with self.assertRaises(ValueError):
            reg.register(n, ("DifferentBase", None, None))

    def test_helper_alignment(self):
        # Ensures that helper functions produce the exact canonical names
        # enumerated in the technical architecture document.
        self.assertEqual(anchor_constant("anchor_lead_generation_rate", "Sector_One"), "anchor_lead_generation_rate_Sector_One")
        self.assertEqual(product_constant("price", "Product_One"), "price_Product_One")
        self.assertEqual(price_lookup_name_product("Product_One"), "price_Product_One")
        self.assertEqual(anchor_lead_generation("Sector_Two"), "Anchor_Lead_Generation_Sector_Two")


if __name__ == "__main__":
    unittest.main()
