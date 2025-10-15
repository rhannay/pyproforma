#!/usr/bin/env python3
"""
Demo script showing the new LineItemsResults.move() method functionality.

This script demonstrates how to use the new move() method that was added to
LineItemsResults, which allows moving multiple line items as a group while
preserving their relative order.
"""

from pyproforma import LineItem, Model


def main():
    # Create a model with several line items
    line_items = [
        LineItem(name="revenue", category="income", values={2023: 1000, 2024: 1200}),
        LineItem(name="cost_of_goods", category="costs", values={2023: 400, 2024: 480}),
        LineItem(
            name="gross_profit", category="income", formula="revenue - cost_of_goods"
        ),
        LineItem(name="marketing", category="costs", values={2023: 150, 2024: 180}),
        LineItem(name="salaries", category="costs", values={2023: 200, 2024: 220}),
        LineItem(
            name="operating_expenses", category="costs", formula="marketing + salaries"
        ),
        LineItem(
            name="net_profit",
            category="income",
            formula="gross_profit - operating_expenses",
        ),
        LineItem(
            name="tax_rate", category="assumptions", values={2023: 0.25, 2024: 0.25}
        ),
        LineItem(name="taxes", category="costs", formula="net_profit * tax_rate"),
        LineItem(name="final_profit", category="income", formula="net_profit - taxes"),
    ]

    model = Model(line_items=line_items, years=[2023, 2024])

    print("=== LineItemsResults.move() Method Demo ===\n")

    # Show initial order
    print("Initial line item order:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Demonstrate moving multiple items to top while preserving their order
    print(
        "Moving all cost-related items ['marketing', 'salaries', "
        "'operating_expenses'] to the top..."
    )
    cost_items = model.line_items(["marketing", "salaries", "operating_expenses"])
    cost_items.move(position="top")

    print("New order after moving cost items to top:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Demonstrate moving items after a target
    print(
        "Moving assumptions and tax items ['tax_rate', 'taxes'] after 'net_profit'..."
    )
    tax_items = model.line_items(["tax_rate", "taxes"])
    tax_items.move(position="after", target="net_profit")

    print("New order after moving tax items after net_profit:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Demonstrate moving items to specific index
    print("Moving revenue items ['revenue', 'gross_profit'] to index 0...")
    revenue_items = model.line_items(["revenue", "gross_profit"])
    revenue_items.move(position="index", index=0)

    print("New order after moving revenue items to index 0:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Demonstrate moving items to bottom
    print("Moving final calculations ['final_profit'] to the bottom...")
    final_items = model.line_items(["final_profit"])
    final_items.move(position="bottom")

    print("Final order after moving final_profit to bottom:")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    # Show that functionality is preserved
    print("Values and calculations are still correct after moving:")
    print(f"  Final Profit 2024: {model.value('final_profit', 2024)}")
    print(f"  Operating Expenses 2024: {model.value('operating_expenses', 2024)}")
    print(f"  Net Profit 2024: {model.value('net_profit', 2024)}")
    print()

    # Demonstrate preserving order when specifying items in different order
    print(
        "Moving items in custom order ['taxes', 'tax_rate'] (reversed) "
        "to position after gross_profit..."
    )
    tax_items_reversed = model.line_items(["taxes", "tax_rate"])
    tax_items_reversed.move(position="after", target="gross_profit")

    print("Final order (note 'taxes' comes before 'tax_rate' as specified):")
    for i, name in enumerate(model.line_item_names):
        print(f"  {i}: {name}")
    print()

    print("=== Demo Complete ===")
    print("The LineItemsResults.move() method successfully repositions multiple")
    print("line items as a group while preserving their relative order and all")
    print("model functionality.")


if __name__ == "__main__":
    main()
