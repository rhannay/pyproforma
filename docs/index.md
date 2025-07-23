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
from pyproforma import Model

# Create a financial model
model = Model()

# Add line items, formulas, etc.
model.add_line_item("revenue", [100, 110, 121])
model.add_line_item("costs", [50, 55, 60])
model.add_formula("profit", "revenue - costs")

# Display results
results = model.calculate()
print(results)
```
