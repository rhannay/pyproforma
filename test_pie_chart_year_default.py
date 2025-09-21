#!/usr/bin/env python3
"""
Test script to verify that line_items_pie works with default year=None parameter.
"""

import os
import sys

# Add the pyproforma package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from pyproforma import LineItem, Model


def test_line_items_pie_with_default_year():
    """Test that line_items_pie works with year=None (using latest year)."""
    print("Testing line_items_pie with default year parameter...")

    # Create a simple model with multiple years
    line_items = [
        LineItem(
            name="revenue",
            label="Revenue",
            category="income",
            values={2020: 100.0, 2021: 150.0, 2022: 200.0},
        ),
        LineItem(
            name="expenses",
            label="Expenses",
            category="costs",
            values={2020: 50.0, 2021: 75.0, 2022: 100.0},
        ),
    ]

    model = Model(line_items=line_items, years=[2020, 2021, 2022])

    # Test 1: Call line_items_pie without year parameter (should use latest year)
    print("Test 1: Calling line_items_pie without year parameter...")
    try:
        fig1 = model.charts.line_items_pie(["revenue", "expenses"])
        print(f"✓ Successfully created pie chart with default year")
        print(f"  Chart title: {fig1.layout.title.text}")

        # Verify the chart is using the latest year (2022)
        expected_title = "Line Items Distribution - 2022"
        if fig1.layout.title.text == expected_title:
            print(f"✓ Chart title correctly shows latest year: {expected_title}")
        else:
            print(
                f"✗ Expected title '{expected_title}', got '{fig1.layout.title.text}'"
            )

    except Exception as e:
        print(f"✗ Error creating pie chart with default year: {e}")
        return False

    # Test 2: Call line_items_pie with explicit year
    print("\nTest 2: Calling line_items_pie with explicit year=2021...")
    try:
        fig2 = model.charts.line_items_pie(["revenue", "expenses"], year=2021)
        print(f"✓ Successfully created pie chart with explicit year")
        print(f"  Chart title: {fig2.layout.title.text}")

        # Verify the chart is using the specified year (2021)
        expected_title = "Line Items Distribution - 2021"
        if fig2.layout.title.text == expected_title:
            print(f"✓ Chart title correctly shows specified year: {expected_title}")
        else:
            print(
                f"✗ Expected title '{expected_title}', got '{fig2.layout.title.text}'"
            )

    except Exception as e:
        print(f"✗ Error creating pie chart with explicit year: {e}")
        return False

    # Test 3: Test CategoryResults.pie_chart with default year
    print("\nTest 3: Testing CategoryResults.pie_chart with default year...")
    try:
        income_category = model.category("income")
        fig3 = income_category.pie_chart()  # No year parameter
        print(f"✓ Successfully created category pie chart with default year")
        print(f"  Chart title: {fig3.layout.title.text}")

    except Exception as e:
        print(f"✗ Error creating category pie chart with default year: {e}")
        return False

    print(
        "\n✓ All tests passed! The line_items_pie method now works correctly with default year=None."
    )
    return True


if __name__ == "__main__":
    success = test_line_items_pie_with_default_year()
    if not success:
        sys.exit(1)
