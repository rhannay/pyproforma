"""
Example: Using scalar values as constants in PyProforma

This example demonstrates how to use scalar values for line items that should
have the same value across all years, such as tax rates, inflation assumptions,
and other financial constants.
"""

from pyproforma import LineItem, Model

# Define the years for our model
years = [2024, 2025, 2026, 2027, 2028]

# ============================================================================
# CONSTANTS - Using scalar values (same value for all years)
# ============================================================================

# Tax rate - just pass a scalar value instead of a dict
tax_rate = LineItem(
    name="tax_rate",
    label="Corporate Tax Rate",
    values=0.21,  # Scalar value - same for all years
)

# Annual inflation assumption
inflation_rate = LineItem(
    name="inflation",
    label="Annual Inflation Rate",
    values=0.03,  # Scalar value
)

# ============================================================================
# REVENUE - Using dict values (different values per year)
# ============================================================================

revenue = LineItem(
    name="revenue",
    label="Revenue",
    values={
        2024: 1000000,
        2025: 1100000,
        2026: 1210000,
        2027: 1331000,
        2028: 1464100,
    },
)

# ============================================================================
# EXPENSES & PROFIT - Using formulas with scalar constants
# ============================================================================

# Operating expenses
opex = LineItem(
    name="opex",
    label="Operating Expenses",
    values={2024: 300000, 2025: 315000, 2026: 330750, 2027: 347287, 2028: 364652},
)

# EBIT (Earnings Before Interest and Tax)
ebit = LineItem(
    name="ebit",
    label="EBIT",
    formula="revenue - opex",
)

# Tax expense - uses the scalar tax_rate constant
tax_expense = LineItem(
    name="tax_expense",
    label="Tax Expense",
    formula="ebit * tax_rate",  # tax_rate is a scalar, same for all years
)

# Net Income
net_income = LineItem(
    name="net_income",
    label="Net Income",
    formula="ebit - tax_expense",
)

# ============================================================================
# CREATE THE MODEL
# ============================================================================

model = Model(
    line_items=[
        tax_rate,
        inflation_rate,
        revenue,
        opex,
        ebit,
        tax_expense,
        net_income,
    ],
    years=years,
)

# ============================================================================
# DEMONSTRATE USAGE
# ============================================================================

if __name__ == "__main__":
    print("PyProforma Scalar Values Example")
    print("=" * 60)
    print()

    # Show scalar values are the same across all years
    print("SCALAR CONSTANTS (Same value across all years):")
    print("-" * 60)
    print(f"Tax Rate:        {model.value('tax_rate', 2024):.1%}")
    print(f"Inflation:       {model.value('inflation', 2024):.1%}")
    print()

    # Verify scalars are consistent across all years
    print("Verifying scalars are consistent:")
    print("-" * 60)
    for year in years:
        assert model.value("tax_rate", year) == 0.21
        assert model.value("inflation", year) == 0.03
    print("✓ All scalars verified to be consistent across all years")
    print()

    # Show calculated values using scalars
    print("CALCULATIONS USING SCALAR CONSTANTS:")
    print("-" * 60)
    for year in years:
        revenue_val = model.value("revenue", year)
        ebit_val = model.value("ebit", year)
        tax = model.value("tax_expense", year)
        net = model.value("net_income", year)

        print(f"\n{year}:")
        print(f"  Revenue:           ${revenue_val:,.0f}")
        print(f"  EBIT:              ${ebit_val:,.0f}")
        print(f"  Tax (21%):         ${tax:,.0f}")
        print(f"  Net Income:        ${net:,.0f}")

    print()
    print("=" * 60)
    print("Example complete!")
    print()
    print("Key Point:")
    print("  - Use scalar values (e.g., values=0.21) for constants")
    print("  - Use dict values (e.g., values={2024: 100}) for year-specific values")
    print("  - Scalars automatically apply to all years in the model")
