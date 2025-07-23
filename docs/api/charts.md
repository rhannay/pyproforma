# Charts API

The Charts API provides functionality for visualizing financial model data through interactive charts.

## Chart Class

The `Chart` class is the base class for all chart types.

```python
from pyproforma.charts import Chart
```

### Methods

#### add_series

Add a data series to the chart.

```python
chart.add_series(name, source, color=None)
```

**Parameters:**

- `name` (str): The name of the data series
- `source` (str): The name of the line item to use as the data source
- `color` (str, optional): The color to use for this series

#### generate

Generate the chart from model results.

```python
chart.generate(results)
```

**Parameters:**

- `results` (Results): The results object from a calculated model

#### show

Display the chart in a browser.

```python
chart.show()
```

#### save

Save the chart to a file.

```python
chart.save(filename)
```

**Parameters:**

- `filename` (str): The name of the file to save the chart to

## LineChart Class

The `LineChart` class creates line charts.

```python
from pyproforma.charts import LineChart

chart = LineChart("Revenue Growth")
chart.add_series("Revenue", "revenue")
chart.generate(results)
chart.show()
```

## BarChart Class

The `BarChart` class creates bar charts.

```python
from pyproforma.charts import BarChart

chart = BarChart("Expense Breakdown")
chart.add_series("Marketing", "marketing_expense")
chart.add_series("R&D", "rd_expense")
chart.add_series("Admin", "admin_expense")
chart.generate(results)
chart.show()
```

## StackedBarChart Class

The `StackedBarChart` class creates stacked bar charts.

```python
from pyproforma.charts import StackedBarChart

chart = StackedBarChart("Revenue by Product")
chart.add_series("Product A", "product_a_revenue")
chart.add_series("Product B", "product_b_revenue")
chart.add_series("Product C", "product_c_revenue")
chart.generate(results)
chart.show()
```

## PieChart Class

The `PieChart` class creates pie charts for a specific period.

```python
from pyproforma.charts import PieChart

chart = PieChart("Revenue Distribution (Year 3)", period=2)
chart.add_series("Product A", "product_a_revenue")
chart.add_series("Product B", "product_b_revenue")
chart.add_series("Product C", "product_c_revenue")
chart.generate(results)
chart.show()
```

## WaterfallChart Class

The `WaterfallChart` class creates waterfall charts to show how a value changes over time.

```python
from pyproforma.charts import WaterfallChart

chart = WaterfallChart("Cash Flow")
chart.add_series("Starting Balance", "starting_balance")
chart.add_series("Revenue", "revenue")
chart.add_series("Expenses", "expenses", is_negative=True)
chart.add_series("Capital Expenditure", "capex", is_negative=True)
chart.add_series("Financing", "financing")
chart.add_series("Ending Balance", "ending_balance", is_total=True)
chart.generate(results)
chart.show()
```

## Advanced Configuration

Charts can be customized with additional options:

```python
chart = LineChart("Revenue Growth")
chart.add_series("Revenue", "revenue", color="#1f77b4")
chart.add_series("Expenses", "expenses", color="#ff7f0e")

# Set chart options
chart.set_option("title", "Revenue and Expenses Over Time")
chart.set_option("x_axis_title", "Year")
chart.set_option("y_axis_title", "Amount ($)")
chart.set_option("legend_position", "bottom")
chart.set_option("height", 600)
chart.set_option("width", 800)

chart.generate(results)
chart.show()
```

## Example: Creating a Dashboard

You can combine multiple charts to create a dashboard:

```python
from pyproforma.charts import LineChart, BarChart, PieChart, Dashboard

# Create individual charts
revenue_chart = LineChart("Revenue Growth")
revenue_chart.add_series("Revenue", "revenue")

profit_chart = LineChart("Profit Margin")
profit_chart.add_series("Profit Margin", "profit_margin")

expense_chart = BarChart("Expense Breakdown")
expense_chart.add_series("Marketing", "marketing_expense")
expense_chart.add_series("R&D", "rd_expense")
expense_chart.add_series("Admin", "admin_expense")

# Generate charts
revenue_chart.generate(results)
profit_chart.generate(results)
expense_chart.generate(results)

# Create a dashboard
dashboard = Dashboard("Financial Performance")
dashboard.add_chart(revenue_chart, row=0, col=0)
dashboard.add_chart(profit_chart, row=0, col=1)
dashboard.add_chart(expense_chart, row=1, col=0, colspan=2)

# Display or save the dashboard
dashboard.show()
dashboard.save("financial_dashboard.html")
```
