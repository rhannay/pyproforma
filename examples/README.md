# PyProforma Examples

This directory contains example models demonstrating various features and use cases of PyProforma.

## Available Examples

### `simple_model_1` - Basic Model
A straightforward financial model demonstrating:
- Basic line items with explicit values
- Simple formula calculations
- Revenue, expenses, and net revenue structure

**Structure:**
- Revenue: 5 years of revenue data
- Expenses: 5 years of expense data  
- Net Revenue: Calculated as `revenue - expenses`

### `simple_model_2` - Comprehensive Model
A more complex financial model demonstrating:
- Multiple revenue streams
- Multiple expense categories
- Category-based organization
- Category totals using the `category_total:` formula syntax
- Proper category structure to avoid circular references

**Structure:**
- **Revenue Items:** Product sales, service revenue, licensing fees
- **Expense Items:** Salaries, marketing, rent/utilities, technology
- **Category Totals:** Total revenues and total expenses using category_total formulas
- **Profit Calculation:** EBITDA calculated from category totals

## Usage

```python
from examples import simple_model_1, simple_model_2

# Use the basic model
print(simple_model_1.to_dataframe())

# Use the comprehensive model
print(simple_model_2.to_dataframe())

# Or import directly from specific files
from examples.simple_model_1 import simple_model_1
from examples.simple_model_2 import simple_model_2

# Access specific line items
revenue_item = simple_model_1.line_item('revenue')
print(revenue_item.values)

# Work with categories in the comprehensive model
revenue_items = simple_model_2.line_items(['product_sales', 'service_revenue'])
revenue_table = revenue_items.table()
```

## Key Learning Points

1. **Basic Model Structure:** `simple_model_1` shows the minimal setup needed
2. **Category Organization:** `simple_model_2` demonstrates proper category usage
3. **Formula Calculations:** Both models show different types of formulas
4. **Category Totals:** `simple_model_2` shows how to use `category_total:` syntax
5. **Circular Reference Avoidance:** Total line items use "calculated" category

## Files

- `simple_model_1.py` - Contains the basic model definition
- `simple_model_2.py` - Contains the comprehensive model definition  
- `__init__.py` - Package initialization and exports
- `README.md` - This documentation file