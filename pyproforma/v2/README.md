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
Represents simple values that can be constants or vary by period.

```python
# Constant assumption
tax_rate = Assumption(value=0.21)

# Period-varying assumption
growth_rate = Assumption(values={2024: 0.1, 2025: 0.12, 2026: 0.11})
```

## Current Status

**This is scaffolding only.** The classes are implemented with basic structure and documentation, but:

- ❌ Formula calculation logic is not implemented
- ❌ Model calculation and value resolution is not implemented
- ❌ Integration with existing PyProforma features (tables, charts) is not implemented
- ❌ Tests are not included

The scaffolding provides:

- ✅ Class structure and interfaces
- ✅ Type hints
- ✅ Comprehensive docstrings
- ✅ Basic methods and properties
- ✅ Example usage in `examples/v2_simple_model.py`

## Example

See `examples/v2_simple_model.py` for a complete example of the intended API design.

## Next Steps

To complete the v2 implementation, the following would be needed:

1. Implement formula evaluation and calculation logic
2. Implement value resolution and dependency tracking
3. Add model calculation methods
4. Create comprehensive test suite
5. Integrate with existing PyProforma features (tables, charts)
6. Add documentation and examples
