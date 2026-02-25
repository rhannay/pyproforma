"""
Simple example demonstrating value_format functionality in v2 line items.

This example shows how to use different value formats for different line items,
including percentages, currency, and default number formatting.
"""

from pyproforma.table import Format
from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


class FinancialModel(ProformaModel):
    """
    A simple financial model demonstrating value_format usage.
    """

    # Revenue in currency format with no decimals
    revenue = FixedLine(
        values={2024: 1_000_000, 2025: 1_100_000, 2026: 1_210_000},
        label="Revenue",
        value_format="currency_no_decimals",
    )

    # Growth rate as percentage with two decimals
    growth_rate = FixedLine(
        values={2024: 0.0, 2025: 0.10, 2026: 0.10},
        label="Growth Rate",
        value_format="percent_two_decimals",
    )

    # Margin as percentage
    margin = FixedLine(
        values={2024: 0.25, 2025: 0.25, 2026: 0.25},
        label="Gross Margin",
        value_format="percent",
    )

    # Profit calculated with currency format
    profit = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] * li.margin[t],
        label="Gross Profit",
        value_format=Format.CURRENCY,
    )

    # Operating expenses with default format (no_decimals)
    operating_expenses = FixedLine(
        values={2024: 150_000, 2025: 165_000, 2026: 181_500},
        label="Operating Expenses",
    )

    # Net income calculated with currency format
    net_income = FormulaLine(
        formula=lambda a, li, t: li.profit[t] - li.operating_expenses[t],
        label="Net Income",
        value_format="currency",
    )


def main():
    """Run the example."""
    # Create model instance
    model = FinancialModel(periods=[2024, 2025, 2026])

    # Print header
    print("=" * 70)
    print("Value Format Demonstration")
    print("=" * 70)
    print()

    # Display each line item with its formatted values
    for name in model.line_item_names:
        result = model[name]
        label = result.label or name

        # Show the value format being used
        format_info = result.value_format
        if format_info.prefix:
            format_type = f"Currency ({format_info.prefix})"
        elif format_info.suffix == "%":
            format_type = f"Percentage ({format_info.decimals} decimals)"
        else:
            format_type = f"Number ({format_info.decimals} decimals)"

        print(f"{label}:")
        print(f"  Format: {format_type}")
        print(f"  Values:")

        for period, value in result.values.items():
            # Use the format to display the value
            formatted = format_info.format(value)
            print(f"    {period}: {formatted}")
        print()

    # Create a table showing all line items
    print("=" * 70)
    print("Complete Table")
    print("=" * 70)
    table = model.tables.line_items(include_label=True)
    print(table.to_html())


if __name__ == "__main__":
    main()
