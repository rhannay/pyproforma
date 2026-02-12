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
    # Note: Formula calculation not yet implemented in scaffolding
    expenses = FormulaLine(
        formula=lambda: revenue * expense_ratio,
        label="Operating Expenses",
    )

    profit = FormulaLine(
        formula=lambda: revenue - expenses,
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
    print("Line Item Values:")
    print(f"  Revenue: {model.li.revenue}")
    print(f"  Expenses: {model.li.expenses}")
    print(f"  Profit: {model.li.profit}")
    print()

    # Access specific period values
    print("2024 Values:")
    print(f"  Revenue: ${model.li.get('revenue', 2024):,.0f}")
    print(f"  Expenses: ${model.li.get('expenses', 2024):,.0f}")
    print(f"  Profit: ${model.li.get('profit', 2024):,.0f}")
    print()

    print("2025 Values:")
    print(f"  Revenue: ${model.li.get('revenue', 2025):,.0f}")
    print(f"  Expenses: ${model.li.get('expenses', 2025):,.0f}")
    print(f"  Profit: ${model.li.get('profit', 2025):,.0f}")
    print()

    print("2026 Values:")
    print(f"  Revenue: ${model.li.get('revenue', 2026):,.0f}")
    print(f"  Expenses: ${model.li.get('expenses', 2026):,.0f}")
    print(f"  Profit: ${model.li.get('profit', 2026):,.0f}")
