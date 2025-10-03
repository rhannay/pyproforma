# PyProforma

**A Python package for financial modeling and reporting**

PyProforma is a comprehensive Python library designed to simplify the creation, management, and visualization of financial models. It provides tools for building complex financial models, generating reports, and creating interactive visualizations.

## Features

* **Financial Models**: Create sophisticated financial models with formulas, constraints, and line items
* **Excel Integration**: Easily import from and export to Excel files
* **Data Visualization**: Generate beautiful charts for your financial data
* **Report Generation**: Create professional tables and reports

## Installation

```bash
pip install pyproforma
```

## Quick Start

```python
from pyproforma import Model, LineItem

# Create line items
revenue = LineItem(name="revenue", category="income", values={2023: 100, 2024: 110, 2025: 121})
costs = LineItem(name="costs", category="expenses", values={2023: 50, 2024: 55, 2025: 60})
profit = LineItem(name="profit", category="profit", formula="revenue - costs")

# Create a financial model
model = Model(
    line_items=[revenue, costs, profit],
    years=[2023, 2024, 2025]
)

# Access values
print(f"Revenue 2023: ${model.value('revenue', 2023):,}")
print(f"Profit 2024: ${model.value('profit', 2024):,}")

# Create analysis objects
revenue_analysis = model.line_item('revenue')
print(revenue_analysis.values())
```
