#!/usr/bin/env python3
"""
Demo script showing the new LineItemResults.move() method functionality.

This script demonstrates how to use the new move() method that was added to
LineItemResults, which uses the same arguments as Model.reorder_line_items.
"""

from pyproforma import LineItem, Model


def main():
    # Create a simple model with several line items
    line_items = [
        LineItem(name="revenue", category="income", values={2023: 1000, 2024: 1200}),
        LineItem(name="cost_of_goods", category="costs", values={2023: 400, 2024: 480}),
        LineItem(
            name="operating_expenses", category="costs", values={2023: 300, 2024: 350}
        ),
        LineItem(
            name="gross_profit", category="income", formula="revenue - cost_of_goods"
        ),
        LineItem(
            name="net_profit",
            category="income",
            formula="gross_profit - operating_expenses",
        ),
    ]

    model = Model(line_items=line_items, years=[2023, 2024])

    print("=== LineItemResults.move() Method Demo ===\n")

    # Show initial order
    print("Initial line item order:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Demonstrate moving to top
    print("Moving 'net_profit' to the top...")
    net_profit_item = model.line_item("net_profit")
    net_profit_item.move(position="top")

    print("New order after moving net_profit to top:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Demonstrate moving after a target
    print("Moving 'gross_profit' after 'revenue'...")
    gross_profit_item = model.line_item("gross_profit")
    gross_profit_item.move(position="after", target="revenue")

    print("New order after moving gross_profit after revenue:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Demonstrate moving to a specific index
    print("Moving 'operating_expenses' to index 1...")
    operating_expenses_item = model.line_item("operating_expenses")
    operating_expenses_item.move(position="index", index=1)

    print("New order after moving operating_expenses to index 1:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Demonstrate moving to bottom
    print("Moving 'revenue' to the bottom...")
    revenue_item = model.line_item("revenue")
    revenue_item.move(position="bottom")

    print("Final order after moving revenue to bottom:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Show that values are still accessible
    print("Values are still accessible after moving:")
    print(f"  Net Profit 2024: {model.value('net_profit', 2024)}")
    print(f"  Revenue 2024: {model.value('revenue', 2024)}")
    print()

    print("=== Demo Complete ===")
    print("The move() method successfully repositions line items while preserving")
    print("their functionality and relationships within the model.")


if __name__ == "__main__":
    main()
