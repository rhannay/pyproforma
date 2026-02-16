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
    profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.1)
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
Represents a line item calculated using a formula function. Formulas receive three parameters:
- `a` (AssumptionValues): Access assumptions via `a.tax_rate`, `a.growth_rate`
- `li` (LineItemValues): Access line items via `li.revenue[t]`, `li.revenue[t-1]`
- `t` (int): Current period being calculated

Value overrides are supported for specific periods.

```python
expenses = FormulaLine(
    formula=lambda a, li, t: li.revenue[t] * 0.6,
    values={2024: 50000},  # Override for 2024
    label="Operating Expenses"
)

# Time-offset lookback example
growth = FormulaLine(
    formula=lambda a, li, t: (li.revenue[t] - li.revenue[t-1]) / li.revenue[t-1],
    values={2024: 0.0},  # First period has no prior value
    label="YoY Growth %"
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
Abstract base class for all line items. `FixedLine`, `FormulaLine`, and `GeneratorLine` all inherit from this class.
This allows for type checking and ensures consistency across different line item types.

```python
from pyproforma.v2 import LineItem

# Check if something is a line item
isinstance(revenue, LineItem)  # True for FixedLine, FormulaLine, and GeneratorLine
```

### GeneratorLine (ABC)
Abstract base class for line items that produce multiple related fields from a single specification.
Useful for modeling complex financial structures like debt, depreciation, or any scenario where
one input generates multiple related outputs.

Subclasses must implement:
- `field_names` property: List of field names the generator produces
- `generate_fields()` method: Calculate all field values for a given period

Generated fields are named `{generator_name}_{field_name}` and can be accessed in formulas
via `li.{generator_name}_{field_name}[t]`.

```python
# Example: DebtLine generates principal, interest, debt outstanding, and proceeds
class MyModel(ProformaModel):
    interest_rate = Assumption(value=0.05)
    term = Assumption(value=10)
    
    par_amounts = FixedLine(values={2024: 1000000, 2025: 0, 2026: 500000})
    
    # DebtLine is a GeneratorLine subclass
    debt = DebtLine(
        par_amount_name="par_amounts",
        interest_rate_name="interest_rate",
        term_name="term"
    )
    
    # Access generated fields in formulas
    total_debt_service = FormulaLine(
        formula=lambda a, li, t: li.debt_principal[t] + li.debt_interest[t]
    )
```

**Available GeneratorLine Implementations:**
- `DebtLine`: Generates `principal`, `interest`, `debt_outstanding`, and `proceeds` fields for debt financing

See `examples/v2/debt_example.py` for a comprehensive example.

## Automatic Discovery

When you create a subclass of `ProformaModel`, the framework automatically discovers and categorizes
all class attributes:

- `_assumption_names`: List of all `Assumption` attribute names
- `_line_item_names`: List of all `LineItem` (FixedLine/FormulaLine/GeneratorLine) attribute names

```python
class MyModel(ProformaModel):
    tax_rate = Assumption(value=0.21)
    revenue = FixedLine(values={2024: 100})
    profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.1)
    debt = DebtLine(par_amount_name="revenue", interest_rate_name="tax_rate", term_name="tax_rate")

print(MyModel._assumption_names)  # ['tax_rate']
print(MyModel._line_item_names)   # ['revenue', 'profit', 'debt']
# Note: Generated fields like debt_principal are added automatically during calculation
```

## Table Creation

v2 models now support table creation through the `.tables` namespace and individual line item `.table()` methods.

### Simple Table Creation

```python
# Create model
model = MyModel(periods=[2024, 2025, 2026])

# Create a table with all line items
table = model.tables.line_items()

# Create a table with specific line items
table = model.tables.line_items(
    line_items=['revenue', 'profit'],
    include_name=False,
    include_label=True
)

# Create a table for a single line item
revenue_result = model['revenue']
revenue_table = revenue_result.table()

# Export to HTML or Excel
html = table.to_html()
table.to_excel('output.xlsx')
```

### Template-Based Table Creation

v2 now includes row types and template-based table creation similar to v1:

```python
from pyproforma.v2.tables import ItemRow, LabelRow, BlankRow, PercentChangeRow

# Using dict configurations
template = [
    {"row_type": "label", "label": "Income Statement", "bold": True},
    {"row_type": "blank"},
    {"row_type": "item", "name": "revenue"},
    {"row_type": "percent_change", "name": "revenue"},
]
table = model.tables.from_template(template)

# Or using dataclass configurations
template = [
    LabelRow(label="Income Statement", bold=True),
    BlankRow(),
    ItemRow(name="revenue"),
    PercentChangeRow(name="revenue"),
]
table = model.tables.from_template(template)
```

**Available Row Types:**
- `ItemRow`: Display a line item's values
- `LabelRow`: Section headers
- `BlankRow`: Spacing
- `PercentChangeRow`: Period-over-period percent change
- `CumulativeChangeRow`: Cumulative change from base period
- `CumulativePercentChangeRow`: Cumulative percent change from base period
- `LineItemsTotalRow`: Sum of multiple line items

See `examples/v2/tables_example.py` and `examples/v2/from_template_example.py` for more examples.

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
- ✅ Comprehensive test suite (179 tests)
- ✅ Example usage in `examples/v2/simple_model.py`
- ✅ Tables namespace for table creation
- ✅ LineItemResult.table() method for individual line item tables
- ✅ Row types (ItemRow, LabelRow, BlankRow, etc.)
- ✅ Template-based table creation with from_template()
- ✅ **GeneratorLine for multi-field line items**
- ✅ **DebtLine generator for debt financing**

**Not yet implemented:**

- ❌ Integration with charts
- ❌ Advanced dependency tracking with topological sorting
- ❌ Circular reference detection before execution

The v2 API is functional for basic and intermediate financial models, including complex debt
financing scenarios. Formulas can reference other line items, assumptions, generated fields,
and use time offsets for lookback calculations.

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
