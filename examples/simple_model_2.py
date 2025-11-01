"""
Simple Model 2 - Comprehensive financial model example

This module demonstrates a more complex PyProforma model with:
- Multiple revenue streams and expense categories
- Category-based organization with explicit category definitions
- Category totals using the category_total: formula syntax
- Proper category structure to avoid circular references
"""

from pyproforma import Category, LineItem, Model

# Define the years for our 5-year model
years = [2024, 2025, 2026, 2027, 2028]

# Define categories explicitly for category_total functionality
revenues_category = Category(name="revenues", label="Revenues")
expenses_category = Category(name="expenses", label="Expenses")
calculated_category = Category(name="calculated", label="Calculated")
profit_category = Category(name="profit", label="Profit")

categories = [
    revenues_category,
    expenses_category,
    calculated_category,
    profit_category,
]

# Revenue line items
product_sales = LineItem(
    name="product_sales",
    label="Product Sales",
    category="revenues",
    values={2024: 800000, 2025: 920000, 2026: 1058000, 2027: 1216700, 2028: 1399205},
)

service_revenue = LineItem(
    name="service_revenue",
    label="Service Revenue",
    category="revenues",
    values={2024: 300000, 2025: 345000, 2026: 396750, 2027: 456262, 2028: 524702},
)

licensing_fees = LineItem(
    name="licensing_fees",
    label="Licensing Fees",
    category="revenues",
    values={2024: 150000, 2025: 172500, 2026: 198375, 2027: 228131, 2028: 262351},
)

# Category total for revenues using category_total methodology
total_revenues = LineItem(
    name="total_revenues",
    label="Total Revenues",
    category="calculated",
    formula="category_total:revenues",
)

# Expense line items
salaries = LineItem(
    name="salaries",
    label="Salaries & Benefits",
    category="expenses",
    values={2024: 450000, 2025: 495000, 2026: 544500, 2027: 598950, 2028: 658845},
)

marketing = LineItem(
    name="marketing",
    label="Marketing & Advertising",
    category="expenses",
    values={2024: 125000, 2025: 137500, 2026: 151250, 2027: 166375, 2028: 183012},
)

rent_utilities = LineItem(
    name="rent_utilities",
    label="Rent & Utilities",
    category="expenses",
    values={2024: 80000, 2025: 84000, 2026: 88200, 2027: 92610, 2028: 97240},
)

technology = LineItem(
    name="technology",
    label="Technology & Software",
    category="expenses",
    values={2024: 60000, 2025: 66000, 2026: 72600, 2027: 79860, 2028: 87846},
)

# Category total for expenses using category_total methodology
total_expenses = LineItem(
    name="total_expenses",
    label="Total Expenses",
    category="calculated",
    formula="category_total:expenses",
)

# Profit calculation
ebitda = LineItem(
    name="ebitda",
    label="EBITDA",
    category="profit",
    formula="total_revenues - total_expenses",
)

# Create the comprehensive model
simple_model_2 = Model(
    line_items=[
        # Revenue items
        product_sales,
        service_revenue,
        licensing_fees,
        total_revenues,
        # Expense items
        salaries,
        marketing,
        rent_utilities,
        technology,
        total_expenses,
        # Profit
        ebitda,
    ],
    years=years,
    categories=categories,
)
