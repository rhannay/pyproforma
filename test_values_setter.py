#!/usr/bin/env python3
"""
Simple test script to verify that the LineItemResults values setter works correctly.
"""

from pyproforma.models.category import Category
from pyproforma.models.line_item import LineItem
from pyproforma.models.model import Model


def test_values_setter():
    """Test that setting the values property updates the model."""

    # Create a simple model
    line_items = [
        LineItem(
            name="revenue",
            category="income",
            label="Revenue",
            values={2023: 100000, 2024: 120000, 2025: 140000},
        ),
        LineItem(
            name="expenses",
            category="costs",
            label="Expenses",
            values={2023: 60000, 2024: 70000, 2025: 80000},
        ),
    ]

    categories = [
        Category(name="income", label="Income"),
        Category(name="costs", label="Costs"),
    ]

    model = Model(
        line_items=line_items, years=[2023, 2024, 2025], categories=categories
    )

    # Get the LineItemResults object
    revenue_results = model.line_item("revenue")

    # Verify initial values
    print(f"Original values: {revenue_results.values}")
    print(f"Original values from model: {model.line_item_definition('revenue').values}")
    expected_values = {2023: 100000, 2024: 120000, 2025: 140000}
    assert revenue_results.values == expected_values
    expected_values = {2023: 100000, 2024: 120000, 2025: 140000}
    assert model.line_item_definition("revenue").values == expected_values

    # Update the values using the setter
    new_values = {2023: 150000, 2024: 180000, 2025: 210000}
    revenue_results.values = new_values

    # Verify the values were updated both in results and in the model
    print(f"Updated values: {revenue_results.values}")
    print(f"Updated values from model: {model.line_item_definition('revenue').values}")
    assert revenue_results.values == new_values
    assert model.line_item_definition("revenue").values == new_values

    # Verify that creating a new LineItemResults object also has the updated values
    new_revenue_results = model.line_item("revenue")
    print(f"New LineItemResults values: {new_revenue_results.values}")
    assert new_revenue_results.values == new_values

    print("✅ All tests passed! Values setter is working correctly.")


def test_values_setter_category_item():
    """Test that setting the values on a category item raises an error."""

    # Create a simple model
    line_items = [
        LineItem(name="item1", category="test_category", values={2023: 100}),
        LineItem(name="item2", category="test_category", values={2023: 200}),
    ]

    categories = [Category(name="test_category", label="Test Category")]

    model = Model(line_items=line_items, years=[2023], categories=categories)

    # Get the category results using the category method
    category_results = model.category("test_category")

    print(f"Category values: {category_results.values()}")

    # CategoryResults doesn't have a values setter, and values() is a method not property  # noqa: E501
    # This test verifies that LineItemResults.values setter only works on line_items
    # Let's test with an actual category access through line_item_metadata

    # Test that we can't set values through line_item access on category
    # We need to simulate this differently since category has different structure
    from unittest.mock import patch

    # Mock metadata to simulate a category item being accessed as LineItemResults
    mock_metadata = {
        "source_type": "category",
        "label": "Test Category",
        "value_format": "no_decimals",
        "formula": None,
        "hardcoded_values": None,
    }

    with patch.object(model, "_get_item_metadata", return_value=mock_metadata):
        from pyproforma.models.results import LineItemResults

        category_as_line_item = LineItemResults(model, "test_category")

        # Try to set values on category item - should raise error
        try:
            category_as_line_item.values = {2023: 500}
            print("❌ Error: Should have raised ValueError for category item")
            return False
        except ValueError as e:
            expected_error = (
                "Cannot set values on category item 'test_category'. "
                "Only line_item types support values modification."
            )
            if expected_error in str(e):
                print(f"✅ Correctly raised ValueError: {e}")
            else:
                print(f"❌ Wrong error message: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected exception: {e}")
            return False

    print("✅ Category values setter test passed!")
    return True


if __name__ == "__main__":
    test_values_setter()
    print()
    test_values_setter_category_item()
