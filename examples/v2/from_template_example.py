"""
Example demonstrating v2 from_template functionality.

This example shows how to use the new row types and from_template method
in PyProforma v2 models.
"""

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel
from pyproforma.v2.tables import (
    BlankRow,
    CumulativePercentChangeRow,
    ItemRow,
    LabelRow,
    LineItemsTotalRow,
    PercentChangeRow,
)


class FinancialModel(ProformaModel):
    """
    A financial model demonstrating table creation with templates.
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
    print("PyProforma v2 - from_template() Demonstration")
    print("=" * 80)
    print()

    # Example 1: Template using dict configurations
    print("1. Table using dict-based template:")
    print("-" * 80)
    dict_template = [
        {"row_type": "label", "label": "Income Statement", "bold": True},
        {"row_type": "blank"},
        {"row_type": "item", "name": "revenue"},
        {"row_type": "percent_change", "name": "revenue", "label": "YoY Growth %"},
        {"row_type": "blank"},
        {"row_type": "item", "name": "operating_expenses"},
        {"row_type": "item", "name": "ebitda"},
        {"row_type": "item", "name": "tax_expense"},
        {"row_type": "item", "name": "net_income"},
    ]
    table = model.tables.from_template(dict_template)
    print(table.to_html())
    print()

    # Example 2: Template using dataclass configurations
    print("2. Table using dataclass-based template:")
    print("-" * 80)
    dataclass_template = [
        LabelRow(label="Revenue Analysis", bold=True),
        BlankRow(),
        ItemRow(name="revenue"),
        PercentChangeRow(name="revenue", label="YoY Growth %"),
        CumulativePercentChangeRow(name="revenue", label="Total Growth from 2024"),
    ]
    table = model.tables.from_template(dataclass_template, col_labels="Metric")
    print(table.to_html())
    print()

    # Example 3: Template with two label columns
    print("3. Table with Name and Label columns:")
    print("-" * 80)
    template = [
        {"row_type": "item", "name": "revenue"},
        {"row_type": "item", "name": "ebitda"},
        {"row_type": "item", "name": "net_income"},
        {"row_type": "blank"},
        {
            "row_type": "line_items_total",
            "line_item_names": ["revenue", "ebitda", "net_income"],
            "label": "Combined Total",
        },
    ]
    table = model.tables.from_template(template, col_labels=["Name", "Label"])
    print(table.to_html())
    print()

    # Example 4: Mixed dict and dataclass configurations
    print("4. Table with mixed configuration types:")
    print("-" * 80)
    mixed_template = [
        LabelRow(label="Key Metrics", bold=True),
        {"row_type": "item", "name": "revenue"},
        ItemRow(name="net_income"),
        {"row_type": "blank"},
        LineItemsTotalRow(
            line_item_names=["revenue", "net_income"], label="Total", bold=True
        ),
    ]
    table = model.tables.from_template(mixed_template)
    print(table.to_html())
    print()

    print("=" * 80)
    print("Tables created successfully using from_template()!")
    print("=" * 80)
