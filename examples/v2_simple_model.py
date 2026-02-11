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
        description="Annual revenue projections",
    )

    # Define calculated values
    # Note: Formula calculation not yet implemented in scaffolding
    expenses = FormulaLine(
        formula=lambda: revenue * expense_ratio,
        label="Operating Expenses",
        description="Calculated as revenue * expense ratio",
    )

    profit = FormulaLine(
        formula=lambda: revenue - expenses,
        label="Net Profit",
        description="Revenue minus expenses",
    )


# Example usage (when calculation is implemented)
if __name__ == "__main__":
    # Create a model instance
    model = SimpleFinancialModel(periods=[2024, 2025, 2026])
    print(f"Created model: {model}")
    print(f"Periods: {model.periods}")

    # The following would work once calculation logic is implemented:
    # print(f"Revenue 2024: {model.revenue.get_value(2024)}")
    # print(f"Profit 2024: {model.profit.get_value(2024)}")
