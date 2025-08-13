# Basic Usage

This guide covers the fundamental operations and concepts in PyProforma.

## Creating a Model

Start by importing the required classes and creating line items and a model:

```python
from pyproforma import Model, LineItem

years = [2022, 2023, 2024]

revenue = LineItem(
    name="revenue",
    category="income",
    values={
        2022: 121000, 
        2023: 133100,
        2024: 146410
    }
)

expense = LineItem(
    name="expenses", 
    category="costs",
    values={
        2022: 90000,
        2023: 95000, 
        2024: 100000
    }
)

net_income = LineItem(
    name="net_income",
    category="profit", 
    formula="revenue - expenses"
)

model = Model(
    line_items=[revenue, expense, net_income],
    years=years
)
```
