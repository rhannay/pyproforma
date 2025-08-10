# Basic Usage

This guide covers the fundamental operations and concepts in PyProforma.

## Creating a Model

Start by importing the `Model` class and creating a new instance:

```python
from pyproforma import Model

model = Model()
```

## Working with Line Items

Line items are the basic building blocks of your financial model. They represent time series data like revenue, expenses, etc.

### Adding Line Items

```python
# Add a line item with values for 3 periods
model.add_line_item("revenue", [100, 120, 150])

# Add a line item with no initial values (will be calculated later)
model.add_line_item("profit")

# Add a line item with metadata
model.add_line_item(
    "expenses", 
    [60, 70, 85], 
    metadata={"category": "operating", "currency": "USD"}
)
```

### Accessing Line Items

```python
revenue = model.get_line_item("revenue")
print(revenue.values)  # [100, 120, 150]
```

## Working with Formulas

Formulas define calculations between different line items.

### Adding Formulas

```python
# Simple arithmetic formula
model.add_formula("profit", "revenue - expenses")

# More complex formula with functions
model.add_formula("growth_rate", "if(lag(revenue) > 0, revenue / lag(revenue) - 1, 0)")
```

## Calculating the Model

To run all calculations and get the results:

```python
results = model.calculate()

# Access calculated values
profit = results.get_value("profit")
print(profit)  # [40, 50, 65]
```

## Working with Tables

Tables help organize and display your model data:

```python
from pyproforma.tables import Table

# Create a table
table = Table("Income Statement")

# Add rows from the model
table.add_row("Revenue", "revenue")
table.add_row("Expenses", "expenses")
table.add_row("Profit", "profit")

# Generate the table from model results
table_data = table.generate(results)

# Export to Excel
table.to_excel("income_statement.xlsx", results)
```

## Creating Charts

Visualize your model data with charts:

```python
from pyproforma.charts import LineChart

# Create a chart
chart = LineChart("Revenue and Expenses")

# Add series
chart.add_series("Revenue", "revenue")
chart.add_series("Expenses", "expenses")

# Generate and display the chart
chart.generate(results)
chart.show()

# Save to file
chart.save("revenue_expenses_chart.html")
```

## Next Steps

Explore the [API Reference](../api/model.md) for detailed information on all available classes and methods.
