"""
Advanced example of PyProforma v2 API with time-offset lookback.

This example demonstrates:
- Fixed line items
- Formula lines with dependencies
- Assumptions
- Time-offset lookback references (e.g., revenue[-1])
- Value overrides
"""

from pyproforma.v2 import Assumption, FixedLine, FormulaLine, ProformaModel


class AdvancedFinancialModel(ProformaModel):
    """
    A more advanced financial model demonstrating time offsets and lookbacks.

    This model calculates:
    - Revenue with year-over-year growth
    - Operating expenses as a percentage of revenue
    - EBITDA (revenue - expenses)
    - Year-over-year growth rate
    - Cumulative profit
    """

    # Define assumptions
    expense_ratio = Assumption(value=0.55, label="Operating Expense Ratio")
    tax_rate = Assumption(value=0.21, label="Corporate Tax Rate")

    # Define base revenue for first year
    revenue = FixedLine(
        values={2024: 100000, 2025: 115000, 2026: 132000, 2027: 152000},
        label="Revenue",
    )

    # Calculate operating expenses
    operating_expenses = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] * a.expense_ratio,
        label="Operating Expenses",
    )

    # Calculate EBITDA
    ebitda = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] - li.operating_expenses[t],
        label="EBITDA",
    )

    # Calculate tax expense
    tax_expense = FormulaLine(
        formula=lambda a, li, t: li.ebitda[t] * a.tax_rate,
        label="Tax Expense",
    )

    # Calculate net income
    net_income = FormulaLine(
        formula=lambda a, li, t: li.ebitda[t] - li.tax_expense[t],
        label="Net Income",
    )

    # Calculate YoY growth rate (with override for first year)
    yoy_growth = FormulaLine(
        formula=lambda a, li, t: (li.revenue[t] - li.revenue[t - 1])
        / li.revenue[t - 1],
        values={2024: 0.0},  # First year has no prior year
        label="YoY Revenue Growth %",
    )


if __name__ == "__main__":
    # Create the model
    model = AdvancedFinancialModel(periods=[2024, 2025, 2026, 2027])

    print("=" * 60)
    print("Advanced Financial Model - v2 API Demonstration")
    print("=" * 60)
    print()

    # Display assumptions
    print("Model Assumptions:")
    print(f"  Operating Expense Ratio: {model.av.expense_ratio:.1%}")
    print(f"  Corporate Tax Rate: {model.av.tax_rate:.1%}")
    print()

    # Display income statement for each year
    for year in model.periods:
        print(f"{year} Income Statement:")
        print(f"  Revenue:              ${model.li.get('revenue', year):>12,.0f}")
        print(f"  Operating Expenses:   ${model.li.get('operating_expenses', year):>12,.0f}")
        print(f"  EBITDA:               ${model.li.get('ebitda', year):>12,.0f}")
        print(f"  Tax Expense:          ${model.li.get('tax_expense', year):>12,.0f}")
        print(f"  Net Income:           ${model.li.get('net_income', year):>12,.0f}")
        print()

    # Display growth metrics
    print("Growth Metrics:")
    for year in model.periods:
        growth = model.li.get("yoy_growth", year)
        print(f"  {year} YoY Growth:        {growth:>7.1%}")
    print()

    print("=" * 60)
    print("Model successfully calculated using v2 API!")
    print("=" * 60)
