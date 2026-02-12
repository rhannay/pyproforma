# PyProforma v2 API

This directory contains the scaffolding for version 2 of the PyProforma API, which provides a cleaner, Pydantic-inspired interface for building financial models.

## Overview

Version 2 introduces a class-based approach where users define models by subclassing `ProformaModel` and declaring line items as class attributes. This is inspired by Pydantic's design pattern.

## Core Components

### ProformaModel
Base class for user-defined financial models. Users subclass this and declare line items as class attributes.

```python
class MyModel(ProformaModel):
    revenue = FixedLine(values={2024: 100, 2025: 110})
    profit = FormulaLine(formula=lambda: revenue * 0.1)
```

### FixedLine
Represents a line item with explicit values for each period.

```python
revenue = FixedLine(
    values={2024: 100000, 2025: 110000, 2026: 121000},
    label="Revenue"
)
```

### FormulaLine
Represents a line item calculated using a formula function. Supports value overrides for specific periods.

```python
expenses = FormulaLine(
    formula=lambda: revenue * 0.6,
    values={2024: 50000},  # Override for 2024
    label="Operating Expenses"
)
```

### Assumption
Represents simple scalar values that apply across all periods.

```python
# Simple assumption
tax_rate = Assumption(value=0.21)

# Assumption with label
growth_rate = Assumption(value=0.1, label="Annual Growth Rate")
```

### LineItem (ABC)
Abstract base class for all line items. Both `FixedLine` and `FormulaLine` inherit from this class.
This allows for type checking and ensures consistency across different line item types.

```python
from pyproforma.v2 import LineItem

# Check if something is a line item
isinstance(revenue, LineItem)  # True for FixedLine and FormulaLine
```

## Automatic Discovery

When you create a subclass of `ProformaModel`, the framework automatically discovers and categorizes
all class attributes:

- `_assumption_names`: List of all `Assumption` attribute names
- `_line_item_names`: List of all `LineItem` (FixedLine/FormulaLine) attribute names

```python
class MyModel(ProformaModel):
    tax_rate = Assumption(value=0.21)
    revenue = FixedLine(values={2024: 100})
    profit = FormulaLine(formula=lambda: revenue * 0.1)

print(MyModel._assumption_names)  # ['tax_rate']
print(MyModel._line_item_names)   # ['revenue', 'profit']
```

## Current Status

**Implemented features:**

- ✅ Class structure and interfaces
- ✅ Type hints
- ✅ Comprehensive docstrings
- ✅ Basic methods and properties
- ✅ Formula calculation logic
- ✅ Model calculation and value resolution
- ✅ Dependency tracking (sequential evaluation)
- ✅ Time-offset lookback references (e.g., `revenue[-1]`)
- ✅ AssumptionValues and LineItemValues containers
- ✅ Comprehensive test suite (46 tests)
- ✅ Example usage in `examples/v2/simple_model.py`

**Not yet implemented:**

- ❌ Integration with existing PyProforma features (tables, charts)
- ❌ Advanced dependency tracking with topological sorting
- ❌ Circular reference detection before execution

The v2 API is functional for basic and intermediate financial models. Formulas can reference
other line items, assumptions, and use time offsets for lookback calculations.

## Example

See `examples/v2_simple_model.py` for a complete example of the intended API design.

## Next Steps

To enhance the v2 implementation further, the following could be added:

1. ~~Implement formula evaluation and calculation logic~~ ✅ Done
2. ~~Implement value resolution and dependency tracking~~ ✅ Done (sequential)
3. ~~Add model calculation methods~~ ✅ Done
4. ~~Create comprehensive test suite~~ ✅ Done
5. Integrate with existing PyProforma features (tables, charts)
6. Add advanced dependency tracking with topological sorting
7. Add pre-execution circular reference detection
8. Add documentation and more examples
