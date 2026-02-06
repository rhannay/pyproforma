"""
Constants Example - Using constants for financial assumptions

This example demonstrates how to use constants in PyProforma for values that
remain consistent across all years, such as tax rates, inflation assumptions,
growth rates, and other financial parameters.
"""

from pyproforma import Category, LineItem, Model

# Define the years for our model
years = [2024, 2025, 2026, 2027, 2028]

# Define categories
assumptions = Category(name="assumptions", label="Assumptions")
revenue_cat = Category(name="revenue", label="Revenue")
expenses_cat = Category(name="expenses", label="Expenses")
profit_cat = Category(name="profit", label="Profit & Margins")

categories = [assumptions, revenue_cat, expenses_cat, profit_cat]

# ============================================================================
# CONSTANTS - Values that remain the same across all years
# ============================================================================

# Tax rate assumption - constant across all years
tax_rate = LineItem(
    name="tax_rate",
    label="Corporate Tax Rate",
    category="assumptions",
    constant=0.21,  # 21% tax rate
)

# Annual inflation assumption
inflation_rate = LineItem(
    name="inflation",
    label="Annual Inflation Rate",
    category="assumptions",
    constant=0.03,  # 3% inflation
)

# Cost of goods sold as a percentage of revenue
cogs_percentage = LineItem(
    name="cogs_pct",
    label="COGS % of Revenue",
    category="assumptions",
    constant=0.40,  # 40% of revenue
)

# Operating expense growth rate
opex_growth = LineItem(
    name="opex_growth",
    label="OpEx Growth Rate",
    category="assumptions",
    constant=0.05,  # 5% annual growth
)

# ============================================================================
# REVENUE - Base revenue with year-over-year growth
# ============================================================================

# Starting with base revenue values
base_revenue = LineItem(
    name="revenue",
    label="Revenue",
    category="revenue",
    values={
        2024: 1000000,
        2025: 1100000,
        2026: 1210000,
        2027: 1331000,
        2028: 1464100,
    },
)

# ============================================================================
# EXPENSES - Using constants in formulas
# ============================================================================

# Cost of Goods Sold - uses the constant cogs_percentage
cogs = LineItem(
    name="cogs",
    label="Cost of Goods Sold",
    category="expenses",
    formula="revenue * cogs_pct",
)

# Base operating expenses for first year
base_opex = LineItem(
    name="base_opex",
    label="Base Operating Expenses",
    category="expenses",
    values={2024: 300000},
)

# Operating expenses growing each year using the constant growth rate
# For years after 2024, we apply the constant growth rate
opex_2025 = LineItem(
    name="opex_2025",
    label="Operating Expenses 2025",
    category="expenses",
    formula="base_opex * (1 + opex_growth)",
)

opex_2026 = LineItem(
    name="opex_2026",
    label="Operating Expenses 2026",
    category="expenses",
    formula="opex_2025 * (1 + opex_growth)",
)

opex_2027 = LineItem(
    name="opex_2027",
    label="Operating Expenses 2027",
    category="expenses",
    formula="opex_2026 * (1 + opex_growth)",
)

opex_2028 = LineItem(
    name="opex_2028",
    label="Operating Expenses 2028",
    category="expenses",
    formula="opex_2027 * (1 + opex_growth)",
)

# ============================================================================
# PROFIT CALCULATIONS - Using constants for tax calculations
# ============================================================================

# Gross Profit
gross_profit = LineItem(
    name="gross_profit",
    label="Gross Profit",
    category="profit",
    formula="revenue - cogs",
)

# Operating Income (EBIT)
ebit = LineItem(
    name="ebit",
    label="Operating Income (EBIT)",
    category="profit",
    formula="gross_profit - base_opex",
)

# For simplicity, using base_opex as a proxy for total opex in this formula
# In a real model, you'd sum all opex line items

# Tax Expense - uses the constant tax_rate
tax_expense = LineItem(
    name="tax_expense",
    label="Tax Expense",
    category="profit",
    formula="ebit * tax_rate",
)

# Net Income
net_income = LineItem(
    name="net_income",
    label="Net Income",
    category="profit",
    formula="ebit - tax_expense",
)

# Profit Margin - this will also implicitly use our constants through the formulas
profit_margin = LineItem(
    name="profit_margin",
    label="Profit Margin %",
    category="profit",
    formula="net_income / revenue",
)

# ============================================================================
# CREATE THE MODEL
# ============================================================================

model_with_constants = Model(
    line_items=[
        # Constants
        tax_rate,
        inflation_rate,
        cogs_percentage,
        opex_growth,
        # Revenue
        base_revenue,
        # Expenses
        cogs,
        base_opex,
        opex_2025,
        opex_2026,
        opex_2027,
        opex_2028,
        # Profit
        gross_profit,
        ebit,
        tax_expense,
        net_income,
        profit_margin,
    ],
    years=years,
    categories=categories,
)

# ============================================================================
# DEMONSTRATE USAGE
# ============================================================================

if __name__ == "__main__":
    print("PyProforma Constants Example")
    print("=" * 60)
    print()

    # Show constant values across all years
    print("CONSTANTS (Same value across all years):")
    print("-" * 60)
    print(f"Tax Rate:        {model_with_constants.value('tax_rate', 2024):.1%}")
    print(f"Inflation:       {model_with_constants.value('inflation', 2024):.1%}")
    print(f"COGS %:          {model_with_constants.value('cogs_pct', 2024):.1%}")
    print(f"OpEx Growth:     {model_with_constants.value('opex_growth', 2024):.1%}")
    print()

    # Verify constants are the same across all years
    print("Verifying constants are consistent across years:")
    print("-" * 60)
    for year in years:
        assert model_with_constants.value("tax_rate", year) == 0.21
        assert model_with_constants.value("inflation", year) == 0.03
    print("✓ All constants verified to be consistent across all years")
    print()

    # Show calculated values that use constants
    print("CALCULATIONS USING CONSTANTS:")
    print("-" * 60)
    for year in years:
        revenue = model_with_constants.value("revenue", year)
        cogs_val = model_with_constants.value("cogs", year)
        gross = model_with_constants.value("gross_profit", year)
        ebit_val = model_with_constants.value("ebit", year)
        tax = model_with_constants.value("tax_expense", year)
        net = model_with_constants.value("net_income", year)

        print(f"\n{year}:")
        print(f"  Revenue:           ${revenue:,.0f}")
        print(f"  COGS (40%):        ${cogs_val:,.0f}")
        print(f"  Gross Profit:      ${gross:,.0f}")
        print(f"  EBIT:              ${ebit_val:,.0f}")
        print(f"  Tax (21%):         ${tax:,.0f}")
        print(f"  Net Income:        ${net:,.0f}")

    print()
    print("=" * 60)
    print("Example complete!")
