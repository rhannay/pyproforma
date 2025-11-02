"""
Simple Model 1 - Basic financial model example

This module demonstrates a basic PyProforma model with:
- Single revenue and expense line items
- Simple formula calculations
- Basic category structure
"""

from pyproforma import LineItem, Model

# Define the years for our 5-year model
years = [2024, 2025, 2026, 2027, 2028]

# Create revenue line item with 5 years of data
revenue = LineItem(
    name="revenue",
    label="Revenue",
    category="income",
    values={2024: 1000000, 2025: 1150000, 2026: 1322500, 2027: 1520875, 2028: 1749006},
)

# Create expenses line item with 5 years of data
expenses = LineItem(
    name="expenses",
    label="Operating Expenses",
    category="costs",
    values={2024: 750000, 2025: 825000, 2026: 907500, 2027: 998250, 2028: 1098075},
)

# Create net revenue using a formula
net_revenue = LineItem(
    name="net_revenue",
    label="Net Revenue",
    category="profit",
    formula="revenue - expenses",
)

# Create the simple model
simple_model_1 = Model(line_items=[revenue, expenses, net_revenue], years=years)
