"""
Example usage of PyProforma v2 API.

This example demonstrates how to use the v2 scaffolding to define
a financial model using the Pydantic-inspired class-based approach.
"""

# Note: This is an example showing the intended API design.
# The actual calculation logic is not yet implemented.

from pyproforma.v2 import Assumption, FixedLine, FormulaLine, ProformaModel


class SimpleFinancialModel(ProformaModel):
    """
    A simple financial model demonstrating the v2 API.

    This model includes:
    - Fixed revenue values
    - Calculated expenses based on a formula
    - An assumption for the expense ratio
    """

    # Define assumptions
    expense_ratio = Assumption(value=0.6, label="Expense Ratio")

    # Define fixed values
    revenue = FixedLine(
        values={2024: 100000, 2025: 110000, 2026: 121000},
        label="Revenue",
    )

    # Define calculated values
    expenses = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] * a.expense_ratio,
        label="Operating Expenses",
    )

    profit = FormulaLine(
        formula=lambda a, li, t: li.revenue[t] - li.expenses[t],
        label="Net Profit",
    )


# Example usage (when calculation is implemented)
if __name__ == "__main__":
    # Create a model instance
    model = SimpleFinancialModel(periods=[2024, 2025, 2026])
    print(f"Created model: {model}")
    print(f"Periods: {model.periods}")
    print()

    # Access assumption values
    print("Assumptions:")
    print(f"  Expense Ratio: {model.av.expense_ratio}")
    print()

    # Access calculated line item values
    # Using subscript notation: li.revenue[t]
    print("Line Item Values (using model.li.item[period] notation):")
    print(f"  Revenue 2024: ${model.li.revenue[2024]:,.0f}")
    print(f"  Revenue 2025: ${model.li.revenue[2025]:,.0f}")
    print(f"  Revenue 2026: ${model.li.revenue[2026]:,.0f}")
    print()

    # NEW: Access line items using model['item'] (similar to v1)
    print("Line Item Values (using model['item'][period] notation):")
    revenue = model["revenue"]
    expenses = model["expenses"]
    profit = model["profit"]
    print(f"  Revenue 2024: ${revenue[2024]:,.0f}")
    print(f"  Expenses 2024: ${expenses[2024]:,.0f}")
    print(f"  Profit 2024: ${profit[2024]:,.0f}")
    print()

    # Access specific period values
    print("2024 Income Statement:")
    print(f"  Revenue:   ${model.li.revenue[2024]:>10,.0f}")
    print(f"  Expenses:  ${model.li.expenses[2024]:>10,.0f}")
    print(f"  Profit:    ${model.li.profit[2024]:>10,.0f}")
    print()

    print("2025 Income Statement:")
    print(f"  Revenue:   ${model.li.revenue[2025]:>10,.0f}")
    print(f"  Expenses:  ${model.li.expenses[2025]:>10,.0f}")
    print(f"  Profit:    ${model.li.profit[2025]:>10,.0f}")
    print()

    print("2026 Income Statement:")
    print(f"  Revenue:   ${model.li.revenue[2026]:>10,.0f}")
    print(f"  Expenses:  ${model.li.expenses[2026]:>10,.0f}")
    print(f"  Profit:    ${model.li.profit[2026]:>10,.0f}")
