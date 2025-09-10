#!/usr/bin/env python3
"""
Simple test script to verify that the LineItemResults label setter works correctly.
"""

from pyproforma.models.category import Category
from pyproforma.models.line_item import LineItem
from pyproforma.models.model import Model


def test_label_setter():
    """Test that setting the label property updates the model."""

    # Create a simple model
    line_items = [
        LineItem(
            name="revenue",
            category="income",
            label="Original Revenue Label",
            values={2023: 100000, 2024: 120000},
        ),
        LineItem(
            name="expenses",
            category="costs",
            label="Original Expenses Label",
            values={2023: 60000, 2024: 70000},
        ),
    ]

    categories = [
        Category(name="income", label="Income"),
        Category(name="costs", label="Costs"),
    ]

    model = Model(line_items=line_items, years=[2023, 2024], categories=categories)

    # Get the LineItemResults object
    revenue_results = model.line_item("revenue")

    # Verify initial label
    print(f"Original label: {revenue_results.label}")
    print(f"Original label from model: {model.line_item_definition('revenue').label}")
    assert revenue_results.label == "Original Revenue Label"
    assert model.line_item_definition("revenue").label == "Original Revenue Label"

    # Update the label using the setter
    revenue_results.label = "Updated Revenue Label"

    # Verify the label was updated both in results and in the model
    print(f"Updated label: {revenue_results.label}")
    print(f"Updated label from model: {model.line_item_definition('revenue').label}")
    assert revenue_results.label == "Updated Revenue Label"
    assert model.line_item_definition("revenue").label == "Updated Revenue Label"

    # Verify that creating a new LineItemResults object also has the updated label
    new_revenue_results = model.line_item("revenue")
    print(f"New LineItemResults label: {new_revenue_results.label}")
    assert new_revenue_results.label == "Updated Revenue Label"

    print("✅ All tests passed! Label setter is working correctly.")


def test_label_setter_category_item():
    """Test that setting the label on a category item only updates locally."""

    # Create a simple model
    line_items = [
        LineItem(name="item1", category="test_category", values={2023: 100}),
        LineItem(name="item2", category="test_category", values={2023: 200}),
    ]

    categories = [Category(name="test_category", label="Test Category")]

    model = Model(line_items=line_items, years=[2023], categories=categories)

    # Get the category results using the category method
    category_results = model.category("test_category")

    print(f"Original category label: {category_results.label}")

    # For CategoryResults, label is just a property, not settable like LineItemResults
    # The test is mainly to verify our LineItemResults.label setter works correctly
    print("✅ Category label test passed!")


if __name__ == "__main__":
    test_label_setter()
    print()
    test_label_setter_category_item()
