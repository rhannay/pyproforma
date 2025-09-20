#!/usr/bin/env python3
"""
Quick integration test for the new pie_chart method on CategoryResults.
This test verifies that the pie_chart method works end-to-end.
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from pyproforma import Category, LineItem, Model


def test_pie_chart_integration():
    """Test the pie_chart method integration."""
    print("Testing CategoryResults.pie_chart() integration...")

    # Create test data
    line_items = [
        LineItem(
            name="product_sales",
            category="revenue",
            label="Product Sales",
            values={2023: 100000, 2024: 120000, 2025: 140000},
            value_format="no_decimals",
        ),
        LineItem(
            name="service_revenue",
            category="revenue",
            label="Service Revenue",
            values={2023: 50000, 2024: 60000, 2025: 70000},
            value_format="no_decimals",
        ),
        LineItem(
            name="consulting_fees",
            category="revenue",
            label="Consulting Fees",
            values={2023: 25000, 2024: 30000, 2025: 35000},
            value_format="no_decimals",
        ),
    ]

    categories = [
        Category(name="revenue", label="Revenue", include_total=True),
    ]

    # Create model
    model = Model(
        line_items=line_items,
        years=[2023, 2024, 2025],
        categories=categories,
    )

    # Get category results
    revenue_category = model.category("revenue")

    # Test the pie_chart method
    try:
        fig = revenue_category.pie_chart(year=2023)
        print("✓ pie_chart method successfully returned a figure")

        # Check that it's a plotly figure
        import plotly.graph_objects as go

        assert isinstance(fig, go.Figure), "Expected plotly Figure object"
        print("✓ Returned object is a plotly Figure")

        # Check that the figure has pie chart data
        assert len(fig.data) == 1, "Expected exactly one trace"
        trace = fig.data[0]
        assert trace.type == "pie", "Expected pie chart trace"
        print("✓ Figure contains pie chart trace")

        # Check that the pie chart has the correct labels and values
        expected_labels = ["Product Sales", "Service Revenue", "Consulting Fees"]
        expected_values = [100000, 50000, 25000]

        assert list(trace.labels) == expected_labels, (
            f"Expected labels {expected_labels}, got {list(trace.labels)}"
        )
        assert list(trace.values) == expected_values, (
            f"Expected values {expected_values}, got {list(trace.values)}"
        )
        print("✓ Pie chart has correct labels and values")

        # Test with different year
        fig_2024 = revenue_category.pie_chart(year=2024)
        trace_2024 = fig_2024.data[0]
        expected_values_2024 = [120000, 60000, 30000]
        assert list(trace_2024.values) == expected_values_2024, (
            f"Expected values {expected_values_2024}, got {list(trace_2024.values)}"
        )
        print("✓ Pie chart works correctly for different years")

        # Test custom parameters
        fig_custom = revenue_category.pie_chart(
            year=2023, width=1000, height=800, template="plotly_dark"
        )
        assert fig_custom.layout.width == 1000, "Expected custom width"
        assert fig_custom.layout.height == 800, "Expected custom height"
        assert fig_custom.layout.template.layout.paper_bgcolor == "rgb(17, 17, 17)", (
            "Expected dark template"
        )
        print("✓ Custom parameters work correctly")

        print(
            "\n🎉 All integration tests passed! The pie_chart method is working correctly."
        )
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_error_cases():
    """Test error handling for the pie_chart method."""
    print("\nTesting error cases...")

    # Create model with empty category
    model = Model(years=[2023, 2024])
    model.update.add_category(name="empty", label="Empty Category")

    empty_category = model.category("empty")

    try:
        empty_category.pie_chart(year=2023)
        print("❌ Expected ValueError for empty category")
        return False
    except ValueError as e:
        if "No line items found in category 'empty'" in str(e):
            print("✓ Correctly raised ValueError for empty category")
        else:
            print(f"❌ Unexpected error message: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error type: {e}")
        return False

    return True


if __name__ == "__main__":
    success = test_pie_chart_integration() and test_error_cases()
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
