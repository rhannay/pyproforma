# Working with Line Items

Line items are at the core of PyProforma financial models. They represent individual data points or calculations that form the building blocks of your financial projections. This guide shows you how to create, add, access, and work with line items effectively.

## Creating Line Items

There are several ways to add line items to your model:

### 1. During Model Initialization

You can add line items when creating your model using the `LineItem` helper class:

```python
from pyproforma import Model, LineItem

# Create line items using the LineItem class
revenue = LineItem(
    name="revenue",
    category="income", 
    label="Total Revenue",
    values={2024: 100000, 2025: 115000, 2026: 132250}
)

expenses = LineItem(
    name="expenses",
    category="costs",
    label="Operating Expenses", 
    values={2024: 75000, 2025: 82500, 2026: 90750}
)

profit = LineItem(
    name="profit",
    category="results",
    label="Net Profit",
    formula="revenue - expenses"
)

# Create model with line items
model = Model(
    line_items=[revenue, expenses, profit],
    years=[2024, 2025, 2026]
)
```

### 2. Adding Line Items Incrementally

You can add line items to an existing model using dictionary-style syntax:

```python
# Create empty model first
model = Model(years=[2024, 2025, 2026])

# Add line items incrementally using different approaches
model['revenue'] = [100000, 115000, 132250]  # List of values
model['expenses'] = 75000  # Constant value for all years
model['revenue_growth'] = [0.0, 0.15, 0.15]  # Hardcoded growth rates
model['profit'] = 'revenue - expenses'  # Formula referencing other items
```

### 3. Using the LineItem Class (Optional)

While you can use the `LineItem` helper class, it's not required. 

```python
# With LineItem class
revenue_item = LineItem(
    name="revenue",
    category="income",
    values={2024: 100000, 2025: 115000}
)
model['revenue'] = revenue_item

# Without LineItem class (simpler)
model['revenue'] = [100000, 115000]
```

## Line Item Types

Line items can contain different types of values:

### Hardcoded Values

Direct numerical values for specific years:

```python
# Single value for all years
model['fixed_cost'] = 50000

# List of values (one per year)
model['variable_cost'] = [20000, 22000, 24200]

# Dictionary mapping years to values
model['one_time_expense'] = {2024: 10000, 2025: 0, 2026: 5000}
```

### Formulas

Mathematical expressions that reference other line items:

```python
model['revenue'] = [100000, 115000, 132250]
model['cost_of_goods'] = 'revenue * 0.6'  # 60% of revenue
model['gross_profit'] = 'revenue - cost_of_goods'
model['revenue_multiple'] = 'revenue * 2'  # Simple formula example
```

### Mixed Approaches

You can combine hardcoded values and formulas:

```python
# Set initial values
model['marketing_budget'] = [25000, 30000, 35000]

# Override specific years with formulas
model['marketing_budget'][2026] = 'revenue * 0.25'  # 25% of revenue in 2026
```

## Accessing Line Items

Once line items are in your model, you access them through `LineItemResults` objects using dictionary syntax:

```python
# Access a line item (returns LineItemResults object)
revenue_item = model['revenue']

print(revenue_item.name)      # 'revenue'
print(revenue_item.category)  # 'income'
print(revenue_item.formula)   # None (if hardcoded values)
```

### Getting Values

You can retrieve values for specific years in multiple ways:

```python
# Get value for a specific year
revenue_2024 = model['revenue'][2024]  # Using bracket notation
revenue_2024 = model['revenue'].value(2024)  # Using value() method

# Get all values as a dictionary
all_values = model['revenue'].values  # {2024: 100000, 2025: 115000, 2026: 132250}
```

### LineItemResults Properties

The `LineItemResults` object provides access to line item metadata and methods:

```python
revenue_item = model['revenue']

# Properties
print(revenue_item.name)           # Line item name
print(revenue_item.label)          # Display label
print(revenue_item.category)       # Category
print(revenue_item.formula)        # Formula (if any)
print(revenue_item.source_type)    # 'line_item'
print(revenue_item.values)         # All values as dict

# Check if a year is hardcoded vs calculated
print(revenue_item.is_hardcoded(2024))  # True/False

# Analysis methods
print(revenue_item.percent_change(2025))  # Year-over-year % change
```

## Creating Tables for Line Items

You can quickly create formatted tables for individual line items:

```python
# Create a table for a single line item
revenue_table = model['revenue'].table()
revenue_table  # Displays formatted table in notebook

# Customize table appearance
revenue_table = model['revenue'].table(hardcoded_color='lightblue')
```

The table will show the line item values across all years with proper formatting.

## Creating Charts for Line Items

Generate interactive charts for line items using the `chart()` method:

```python
# Create a line chart for revenue
revenue_chart = model['revenue'].chart()
revenue_chart.show()

# Customize chart appearance
revenue_chart = model['revenue'].chart(
    width=1000,
    height=400,
    chart_type='bar',
    template='plotly_dark'
)

# Save chart as image
revenue_chart.write_image('revenue_trend.png')
```

## Modifying Line Items

You can update line item properties and values after creation:

```python
# Update individual values
model['revenue'][2026] = 140000  # Set specific year value

# Update properties
model['revenue'].label = "Gross Revenue"
model['revenue'].category = "top_line"

# Update formula
model['profit'].formula = "revenue * 0.15"  # Change to 15% margin

# Update all values at once
model['revenue'].values = {2024: 110000, 2025: 125000, 2026: 145000}
```

## Working with Multiple Line Items

Access and work with multiple line items at once:

```python
# Get multiple line items
income_items = model.line_items(['revenue', 'profit'])

# Set category for multiple items
income_items.set_category('financial_results')

# Get individual items from the group
revenue = income_items.line_item('revenue')
```

## Examples in Practice

Here's a complete example showing different line item patterns:

```python
from pyproforma import Model

# Create model with years
model = Model(years=[2024, 2025, 2026])

# Revenue with growth pattern
model['base_revenue'] = [1000000, 1150000, 1322500]

# Expenses as percentage of revenue
model['cost_of_goods'] = 'base_revenue * 0.60'
model['marketing'] = 'base_revenue * 0.15'
model['operations'] = [200000, 220000, 242000]  # Fixed growth

# Calculated results
model['gross_profit'] = 'base_revenue - cost_of_goods'
model['total_expenses'] = 'cost_of_goods + marketing + operations'
model['net_profit'] = 'base_revenue - total_expenses'

# Access and analyze
print(f"2024 Revenue: ${model['base_revenue'][2024]:,}")
print(f"Profit Margin 2026: {model['net_profit'][2026] / model['base_revenue'][2026]:.1%}")

# Create visualizations
model['net_profit'].chart(title="Net Profit Trend").show()
model['base_revenue'].table()
```

This flexible approach allows you to build complex financial models incrementally while maintaining clear access to individual line items for analysis and visualization.