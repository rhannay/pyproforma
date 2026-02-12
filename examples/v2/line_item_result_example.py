"""
Example demonstrating the LineItemResult namespace in v2.

This example shows how to access line item results using the dictionary-style
model['item_name'] syntax, similar to the v1 API.
"""

from pyproforma.v2 import Assumption, FixedLine, FormulaLine, ProformaModel


class SimpleFinancialModel(ProformaModel):
    """A simple financial model with revenue, expenses, and profit."""

    expense_ratio = Assumption(value=0.6, label="Expense Ratio")

    revenue = FixedLine(
        values={2024: 100000, 2025: 110000, 2026: 121000},
        label="Revenue",
    )

    expenses = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] * a.expense_ratio,
        label="Operating Expenses",
    )

    profit = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] - li.expenses[t],
        label="Net Profit",
    )


if __name__ == "__main__":
    # Create a model instance
    model = SimpleFinancialModel(periods=[2024, 2025, 2026])

    print("=" * 60)
    print("LineItemResult Namespace Example")
    print("=" * 60)
    print()

    # Access line items using dictionary-style notation
    print("1. Dictionary-style access (model['revenue']):")
    revenue_result = model["revenue"]
    print(f"   Type: {type(revenue_result).__name__}")
    print(f"   Name: {revenue_result.name}")
    print(f"   Values: {revenue_result.values}")
    print()

    # Access specific period values
    print("2. Access specific period values:")
    print(f"   revenue_result[2024] = {revenue_result[2024]:,}")
    print(f"   revenue_result[2025] = {revenue_result[2025]:,}")
    print(f"   revenue_result[2026] = {revenue_result[2026]:,}")
    print()

    # Access multiple line items
    print("3. Access multiple line items:")
    expenses_result = model["expenses"]
    profit_result = model["profit"]
    print(f"   Revenue 2024: ${revenue_result[2024]:>10,.0f}")
    print(f"   Expenses 2024: ${expenses_result[2024]:>10,.0f}")
    print(f"   Profit 2024: ${profit_result[2024]:>10,.0f}")
    print()

    # Use value() method
    print("4. Use value() method:")
    print(f"   revenue_result.value(2025) = {revenue_result.value(2025):,}")
    print(f"   expenses_result.value(2025) = {expenses_result.value(2025):,}")
    print()

    # String representation
    print("5. String representations:")
    print(f"   repr(revenue_result) = {repr(revenue_result)}")
    print(f"   str(revenue_result) = {str(revenue_result)}")
    print()

    # Traditional access still works
    print("6. Traditional access (model.li.revenue[2024]):")
    print(f"   model.li.revenue[2024] = {model.li.revenue[2024]:,}")
    print()

    print("=" * 60)
    print("Both access patterns work!")
    print("  - model['revenue'][2024]  (new v2 style, similar to v1)")
    print("  - model.li.revenue[2024]  (existing v2 style)")
    print("=" * 60)
