# Models API

The Models API is the core of PyProforma, providing classes for creating and manipulating financial models.

## Quick Start

```python
from pyproforma import Model

# Create a new model
model = Model(periods=5)

# Add line items
model.add_line_item("revenue", [100, 120, 140, 160, 180])
model.add_line_item("expenses", [50, 60, 70, 80, 90])

# Add formula
model.add_formula("profit", "revenue - expenses")

# Calculate the model
results = model.calculate()
```

## API Reference

### Model Class

::: pyproforma.models.model.model.Model

### LineItem Class

::: pyproforma.models.line_item.LineItem

### Constraint Class

::: pyproforma.models.constraint.Constraint

