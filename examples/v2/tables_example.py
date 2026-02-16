"""
Example demonstrating v2 tables functionality.

This example shows how to use the new tables namespace and table() method
in PyProforma v2 models.
"""

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


class FinancialModel(ProformaModel):
    """
    A simple financial model demonstrating table creation.
    """

    revenue = FixedLine(
        values={2024: 100000, 2025: 115000, 2026: 132000, 2027: 152000},
        label="Revenue",
    )

    operating_expenses = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] * 0.55,
        label="Operating Expenses",
    )

    ebitda = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] - li.operating_expenses[t],
        label="EBITDA",
    )

    tax_expense = FormulaLine(
        formula=lambda a, li, t: li.ebitda[t] * 0.21,
        label="Tax Expense",
    )

    net_income = FormulaLine(
        formula=lambda a, li, t: li.ebitda[t] - li.tax_expense[t],
        label="Net Income",
    )


if __name__ == "__main__":
    # Create the model
    model = FinancialModel(periods=[2024, 2025, 2026, 2027])

    print("=" * 80)
    print("PyProforma v2 - Tables Demonstration")
    print("=" * 80)
    print()

    # Example 1: Create a table with all line items (showing names)
    print("1. Table with all line items (showing names):")
    print("-" * 80)
    table = model.tables.line_items()
    print(table.to_html())
    print()

    # Example 2: Create a table with specific line items (showing labels)
    print("2. Table with specific line items (showing labels):")
    print("-" * 80)
    table = model.tables.line_items(
        line_items=["revenue", "ebitda", "net_income"],
        include_name=False,
        include_label=True,
    )
    print(table.to_html())
    print()

    # Example 3: Create a table for a single line item using .table() method
    print("3. Table for a single line item using .table() method:")
    print("-" * 80)
    revenue_result = model["revenue"]
    revenue_table = revenue_result.table()
    print(revenue_table.to_html())
    print()

    # Example 4: Table for a single line item with name included
    print("4. Table for a single line item with name included:")
    print("-" * 80)
    net_income_result = model["net_income"]
    net_income_table = net_income_result.table(include_name=True)
    print(net_income_table.to_html())
    print()

    print("=" * 80)
    print("Tables created successfully!")
    print("=" * 80)
