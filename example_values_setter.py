#!/usr/bin/env python3
"""
Example demonstrating the new LineItemResults.values setter functionality.
"""

from pyproforma import Category, LineItem, Model


def main():
    """Demonstrate the values setter functionality."""

    # Create a simple financial model
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
        LineItem(
            name="profit",
            category="income",
            label="Profit",
            formula="revenue - expenses",
        ),
    ]

    categories = [
        Category(name="income", label="Income"),
        Category(name="costs", label="Costs"),
    ]

    model = Model(
        line_items=line_items, years=[2023, 2024, 2025], categories=categories
    )

    # Get the revenue line item
    revenue = model.line_item("revenue")

    print("=== Original Values ===")
    print(f"Revenue values: {revenue.values}")
    print(f"Profit values: {model.line_item('profit').values}")

    # Update revenue values using the new setter
    print("\n=== Updating Revenue Values ===")
    new_revenue_values = {2023: 150000, 2024: 180000, 2025: 210000}
    revenue.values = new_revenue_values

    print(f"Updated revenue values: {revenue.values}")
    print(f"Updated profit values: {model.line_item('profit').values}")

    # Verify the values are persisted in the model
    print("\n=== Verification ===")
    fresh_revenue = model.line_item("revenue")
    print(f"Fresh revenue values: {fresh_revenue.values}")
    print(f"Model definition values: {model.line_item_definition('revenue').values}")

    print("\n✅ Values setter demonstration complete!")


if __name__ == "__main__":
    main()
