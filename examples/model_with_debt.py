"""
Model with Debt - Example demonstrating debt financing

This module demonstrates a PyProforma model with:
- Basic revenue and expense line items
- Long-term debt using the Debt generator class
- Debt service calculations (principal and interest payments)
- Bond proceeds and debt outstanding tracking
"""

from pyproforma import Category, LineItem, Model
from pyproforma.models.generator import Debt

# Define the years for our 5-year model
years = [2024, 2025, 2026, 2027, 2028]

# Define categories for organization
revenues_category = Category(name="revenues", label="Revenues")
expenses_category = Category(name="expenses", label="Operating Expenses")
debt_service_category = Category(name="debt_service", label="Debt Service")
financing_category = Category(name="financing", label="Financing Activities")

categories = [
    revenues_category,
    expenses_category,
    debt_service_category,
    financing_category,
]

# =============================================================================
# REVENUE AND EXPENSE LINE ITEMS
# =============================================================================

# Revenue line item - growing business
annual_revenue = LineItem(
    name="annual_revenue",
    label="Annual Revenue",
    category="revenues",
    values={
        2024: 2000000,
        2025: 2200000,
        2026: 2420000,
        2027: 2662000,
        2028: 2928200,
    },
)

# Operating expenses - scaled with revenue but more efficient over time
operating_expenses = LineItem(
    name="operating_expenses",
    label="Operating Expenses",
    category="expenses",
    values={
        2024: 1400000,  # 70% of revenue
        2025: 1496000,  # 68% of revenue
        2026: 1573000,  # 65% of revenue
        2027: 1597200,  # 60% of revenue
        2028: 1756920,  # 60% of revenue
    },
)

# =============================================================================
# DEBT FINANCING
# =============================================================================

# Create a debt generator for long-term financing
# This will issue bonds in 2024 and 2026 with 10-year terms at 5% interest
debt_financing = Debt(
    name="debt",
    par_amount={
        2024: 3000000,  # Initial bond issue of $3M
        2025: 0,  # No new debt in 2025
        2026: 1500000,  # Additional bond issue of $1.5M
        2027: 0,  # No new debt in 2027
        2028: 0,  # No new debt in 2028
    },
    interest_rate=0.05,  # 5% annual interest rate
    term=10,  # 10-year term for all bonds
)

# Calculate EBITDA (before debt service)
ebitda = LineItem(
    name="ebitda",
    label="EBITDA",
    category="revenues",
    formula="annual_revenue - operating_expenses",
)

# Net income after debt service
net_income = LineItem(
    name="net_income",
    label="Net Income",
    category="revenues",
    formula="ebitda - debt_interest",
)

# =============================================================================
# CREATE THE MODEL
# =============================================================================

model_with_debt = Model(
    line_items=[
        # Revenue and expenses
        annual_revenue,
        operating_expenses,
        ebitda,
        net_income,
    ],
    generators=[
        # Debt generator - this will create multiple line items:
        # - debt_principal (principal payments)
        # - debt_interest (interest payments)
        # - debt_bond_proceeds (bond issuance proceeds)
        # - debt_debt_outstanding (outstanding debt balance)
        debt_financing,
    ],
    years=years,
    categories=categories,
)
