# Getting Started with PyProforma

This guide will help you get up and running with PyProforma quickly.

## Prerequisites

- Python 3.9 or higher
- Basic understanding of financial modeling concepts

## Installation

Install PyProforma using pip:

```bash
pip install pyproforma
```

## Basic Concepts

PyProforma is built around a few core concepts:

### Models

The `Model` class is the central component of PyProforma. It contains line items, formulas, and constraints that define your financial model.

### Line Items

Line items represent individual financial data points or time series within your model, such as revenue, expenses, or growth rates.

### Formulas

Formulas define calculations between different line items, similar to formulas in a spreadsheet.

### Tables

Tables are used to organize and display your model data in a structured format.

### Charts

Charts provide visualization capabilities for your financial data.

## A Simple Example

Here's a minimal example to demonstrate how PyProforma works:

```python
from pyproforma import Model

# Create a new financial model
model = Model()

# Add line items with projected values for three years
model.add_line_item("revenue", [1000, 1200, 1440])
model.add_line_item("growth_rate", [None, 0.2, 0.2])
model.add_line_item("expenses", [700, 800, 900])

# Add a formula to calculate profit
model.add_formula("profit", "revenue - expenses")
model.add_formula("profit_margin", "profit / revenue")

# Calculate the model
results = model.calculate()

# Display the results
print(results.get_value("profit"))  # [300, 400, 540]
print(results.get_value("profit_margin"))  # [0.3, 0.333, 0.375]
```

## Next Steps

Proceed to the [User Guide](user-guide/installation.md) for more detailed information on how to use PyProforma effectively.
