"""
Working with Line Items - Code Examples

This file contains all the code examples from the documentation file:
docs/user-guide/working-with-line-items.md

These examples demonstrate how to create, add, access, and work with line items
in PyProforma financial models.
"""

from pyproforma import LineItem, Model

print("=" * 60)
print("WORKING WITH LINE ITEMS - CODE EXAMPLES")
print("=" * 60)

# =============================================================================
# SECTION 1: Creating Line Items During Model Initialization
# =============================================================================
print("\n1. Creating Line Items During Model Initialization")
print("-" * 50)

# Create line items using the LineItem class
revenue = LineItem(
    name="revenue",
    category="income",
    label="Total Revenue",
    values={2024: 100000, 2025: 115000, 2026: 132250},
)

expenses = LineItem(
    name="expenses",
    category="costs",
    label="Operating Expenses",
    values={2024: 75000, 2025: 82500, 2026: 90750},
)

profit = LineItem(
    name="profit", category="results", label="Net Profit", formula="revenue - expenses"
)

# Create model with line items
model = Model(line_items=[revenue, expenses, profit], years=[2024, 2025, 2026])

print("Created model with line items:")
print(f"- Revenue 2024: ${model['revenue'][2024]:,}")
print(f"- Expenses 2024: ${model['expenses'][2024]:,}")
print(f"- Profit 2024: ${model['profit'][2024]:,}")

# =============================================================================
# SECTION 2: Adding Line Items Incrementally
# =============================================================================
print("\n\n2. Adding Line Items Incrementally")
print("-" * 50)

# Create empty model first
model2 = Model(years=[2024, 2025, 2026])

# Add line items incrementally using different approaches
model2["revenue"] = [100000, 115000, 132250]  # List of values
model2["expenses"] = 75000  # Constant value for all years
# Note: Growth rate calculation requires more complex setup, so using a simpler example
model2["revenue_growth"] = [0.0, 0.15, 0.15]  # Hardcoded growth rates
model2["profit"] = "revenue - expenses"  # Formula referencing other items

print("Added line items incrementally:")
print(f"- Revenue 2025: ${model2['revenue'][2025]:,}")
print(f"- Expenses (constant): ${model2['expenses'][2024]:,}")
print(f"- Revenue growth 2025: {model2['revenue_growth'][2025]:.1%}")
print(f"- Profit 2025: ${model2['profit'][2025]:,}")

# =============================================================================
# SECTION 3: Using LineItem Class (Optional)
# =============================================================================
print("\n\n3. Using LineItem Class (Optional)")
print("-" * 50)

model3 = Model(years=[2024, 2025])

# With LineItem class
revenue_item = LineItem(
    name="revenue", category="income", values={2024: 100000, 2025: 115000}
)
model3["revenue"] = revenue_item

# Without LineItem class (simpler)
model3["costs"] = [100000, 115000]

print("Comparison of approaches:")
print(f"- Revenue (with LineItem): ${model3['revenue'][2024]:,}")
print(f"- Costs (without LineItem): ${model3['costs'][2024]:,}")

# =============================================================================
# SECTION 4: Line Item Types - Hardcoded Values
# =============================================================================
print("\n\n4. Line Item Types - Hardcoded Values")
print("-" * 50)

model4 = Model(years=[2024, 2025, 2026])

# Single value for all years
model4["fixed_cost"] = 50000

# List of values (one per year)
model4["variable_cost"] = [20000, 22000, 24200]

# Dictionary mapping years to values
model4["one_time_expense"] = {2024: 10000, 2025: 0, 2026: 5000}

print("Hardcoded values:")
print(f"- Fixed cost 2024: ${model4['fixed_cost'][2024]:,}")
print(f"- Variable cost 2025: ${model4['variable_cost'][2025]:,}")
print(f"- One-time expense 2025: ${model4['one_time_expense'][2025]:,}")

# =============================================================================
# SECTION 5: Line Item Types - Formulas
# =============================================================================
print("\n\n5. Line Item Types - Formulas")
print("-" * 50)

model5 = Model(years=[2024, 2025, 2026])

model5["revenue"] = [100000, 115000, 132250]
model5["cost_of_goods"] = "revenue * 0.6"  # 60% of revenue
model5["gross_profit"] = "revenue - cost_of_goods"
# Note: Growth rate calculation using lag values requires special handling
model5["revenue_multiple"] = "revenue * 2"  # Simple formula example

print("Formula calculations:")
print(f"- Revenue 2025: ${model5['revenue'][2025]:,}")
print(f"- Cost of goods 2025: ${model5['cost_of_goods'][2025]:,}")
print(f"- Gross profit 2025: ${model5['gross_profit'][2025]:,}")
print(f"- Revenue multiple 2025: ${model5['revenue_multiple'][2025]:,}")

# =============================================================================
# SECTION 6: Mixed Approaches
# =============================================================================
print("\n\n6. Mixed Approaches")
print("-" * 50)

model6 = Model(years=[2024, 2025, 2026])
model6["revenue"] = [100000, 115000, 132250]

# Set initial values
model6["marketing_budget"] = [25000, 30000, 35000]

# Override specific years with formulas
# Note: This would typically be done after initial setup
print("Initial marketing budget 2026:", model6["marketing_budget"][2026])

# =============================================================================
# SECTION 7: Accessing Line Items
# =============================================================================
print("\n\n7. Accessing Line Items")
print("-" * 50)

# Access a line item (returns LineItemResults object)
revenue_item = model["revenue"]

print("Line item properties:")
print(f"- Name: {revenue_item.name}")
print(f"- Category: {revenue_item.category}")
print(f"- Formula: {revenue_item.formula}")

# =============================================================================
# SECTION 8: Getting Values
# =============================================================================
print("\n\n8. Getting Values")
print("-" * 50)

# Get value for a specific year
revenue_2024 = model["revenue"][2024]  # Using bracket notation
revenue_2024_alt = model["revenue"].value(2024)  # Using value() method

# Get all values as a dictionary
all_values = model["revenue"].values

print("Value access methods:")
print(f"- Revenue 2024 (bracket): ${revenue_2024:,}")
print(f"- Revenue 2024 (method): ${revenue_2024_alt:,}")
print(f"- All values: {all_values}")

# =============================================================================
# SECTION 9: LineItemResults Properties
# =============================================================================
print("\n\n9. LineItemResults Properties")
print("-" * 50)

revenue_item = model["revenue"]

# Properties
print("LineItemResults properties:")
print(f"- Name: {revenue_item.name}")
print(f"- Label: {revenue_item.label}")
print(f"- Category: {revenue_item.category}")
print(f"- Formula: {revenue_item.formula}")
print(f"- Source type: {revenue_item.source_type}")
print(f"- Values: {revenue_item.values}")

# Check if a year is hardcoded vs calculated
print(f"- Is 2024 hardcoded: {revenue_item.is_hardcoded(2024)}")

# Analysis methods
print(f"- Percent change 2025: {revenue_item.percent_change(2025):.1%}")

# =============================================================================
# SECTION 10: Creating Tables for Line Items
# =============================================================================
print("\n\n10. Creating Tables for Line Items")
print("-" * 50)

# Create a table for a single line item
revenue_table = model["revenue"].table()
print("Created revenue table (Table object)")

# Customize table appearance
revenue_table_custom = model["revenue"].table(hardcoded_color="lightblue")
print("Created custom revenue table with hardcoded color")

# =============================================================================
# SECTION 11: Creating Charts for Line Items
# =============================================================================
print("\n\n11. Creating Charts for Line Items")
print("-" * 50)

# Create a line chart for revenue
revenue_chart = model["revenue"].chart()
print("Created revenue chart (Plotly Figure object)")

# Customize chart appearance
revenue_chart_custom = model["revenue"].chart(
    width=1000,
    height=400,
    chart_type="bar",
    template="plotly_white",  # Changed from 'plotly_dark' to avoid potential issues
)
print("Created custom revenue chart")

# Note: chart.show() and write_image() calls are commented out to avoid
# display/file system operations during testing
# revenue_chart.show()
# revenue_chart.write_image('revenue_trend.png')

# =============================================================================
# SECTION 12: Modifying Line Items
# =============================================================================
print("\n\n12. Modifying Line Items")
print("-" * 50)

# Create a test model for modifications
model_mod = Model(years=[2024, 2025, 2026])
model_mod["revenue"] = [100000, 115000, 132250]
model_mod["profit"] = "revenue * 0.1"

print("Before modifications:")
print(f"- Revenue 2026: ${model_mod['revenue'][2026]:,}")
print(f"- Revenue label: {model_mod['revenue'].label}")

# Update individual values
model_mod["revenue"][2026] = 140000  # Set specific year value

# Update properties
model_mod["revenue"].label = "Gross Revenue"
model_mod["revenue"].category = "top_line"

# Update formula
model_mod["profit"].formula = "revenue * 0.15"  # Change to 15% margin

print("After modifications:")
print(f"- Revenue 2026: ${model_mod['revenue'][2026]:,}")
print(f"- Revenue label: {model_mod['revenue'].label}")
print(f"- Revenue category: {model_mod['revenue'].category}")
print(f"- Profit 2024 (15% margin): ${model_mod['profit'][2024]:,}")

# Update all values at once
model_mod["revenue"].values = {2024: 110000, 2025: 125000, 2026: 145000}
print(f"- Revenue 2024 (after values update): ${model_mod['revenue'][2024]:,}")

# =============================================================================
# SECTION 13: Working with Multiple Line Items
# =============================================================================
print("\n\n13. Working with Multiple Line Items")
print("-" * 50)

# Get multiple line items
income_items = model.line_items(["revenue", "profit"])

print("Multiple line items:")
print(f"- Names: {income_items.names}")

# Set category for multiple items
income_items.set_category("financial_results")

# Get individual items from the group
revenue_from_group = income_items.line_item("revenue")
print(f"- Revenue category after group update: {revenue_from_group.category}")

# =============================================================================
# SECTION 14: Complete Example in Practice
# =============================================================================
print("\n\n14. Complete Example in Practice")
print("-" * 50)

# Create model with years
final_model = Model(years=[2024, 2025, 2026])

# Revenue with growth pattern
final_model["base_revenue"] = [1000000, 1150000, 1322500]

# Expenses as percentage of revenue
final_model["cost_of_goods"] = "base_revenue * 0.60"
final_model["marketing"] = "base_revenue * 0.15"
final_model["operations"] = [200000, 220000, 242000]  # Fixed growth

# Calculated results
final_model["gross_profit"] = "base_revenue - cost_of_goods"
final_model["total_expenses"] = "cost_of_goods + marketing + operations"
final_model["net_profit"] = "base_revenue - total_expenses"

# Access and analyze
print("Final Model Results:")
print(f"- 2024 Revenue: ${final_model['base_revenue'][2024]:,}")
print(f"- 2024 Cost of Goods: ${final_model['cost_of_goods'][2024]:,}")
print(f"- 2024 Marketing: ${final_model['marketing'][2024]:,}")
print(f"- 2024 Operations: ${final_model['operations'][2024]:,}")
print(f"- 2024 Net Profit: ${final_model['net_profit'][2024]:,}")

profit_margin_2026 = final_model["net_profit"][2026] / final_model["base_revenue"][2026]
print(f"- Profit Margin 2026: {profit_margin_2026:.1%}")

# Create visualizations (objects created but not displayed)
net_profit_chart = final_model["net_profit"].chart()
base_revenue_table = final_model["base_revenue"].table()

print("- Created net profit chart and base revenue table")

print("\n" + "=" * 60)
print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
print("=" * 60)
