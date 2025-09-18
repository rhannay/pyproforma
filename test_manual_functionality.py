#!/usr/bin/env python3
"""Manual test to verify the new value setting functionality works."""

from pyproforma.models.category import Category
from pyproforma.models.line_item import LineItem
from pyproforma.models.model import Model


def test_value_setting_functionality():
    """Test the new bracket notation and set_value functionality."""

    # Create a simple model
    line_items = [
        LineItem(
            name="revenue",
            category="income",
            label="Revenue",
            values={2023: 100000, 2024: 120000, 2025: 140000},
            value_format="no_decimals",
        )
    ]

    categories = [Category(name="income", label="Income")]

    model = Model(
        line_items=line_items, years=[2023, 2024, 2025], categories=categories
    )

    # Test the new functionality
    revenue = model.line_item("revenue")
    print(f"Original 2024 value: {revenue[2024]}")
    assert revenue[2024] == 120000

    # Test bracket notation assignment (requested feature)
    revenue[2024] = 99999
    print(f"After setting via bracket notation: {revenue[2024]}")
    assert revenue[2024] == 99999

    # Test method assignment
    revenue.set_value(2025, 88888)
    print(f"After setting via method: {revenue[2025]}")
    assert revenue[2025] == 88888

    # Verify other years unchanged
    print(f"2023 value (unchanged): {revenue[2023]}")
    assert revenue[2023] == 100000

    print("✅ All functionality working correctly!")
    return True


if __name__ == "__main__":
    test_value_setting_functionality()
