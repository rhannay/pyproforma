# Pyproforma

A Python package for financial modeling and reporting that provides a flexible framework for building financial models with line items, formulas, constraints, and rich output formatting.

## Installation

Install from PyPI:

```bash
pip install pyproforma
```

For local development:

```bash
pip install -e .
```

## Quick Start

```python
from pyproforma import Model, LineItem, Category

# Create line items
revenue = LineItem(
    name="revenue",
    category="income",
    label="Total Revenue",
    values={2024: 100000, 2025: 120000, 2026: 150000}
)

expenses = LineItem(
    name="expenses", 
    category="income",
    label="Total Expenses",
    formula="revenue * 0.6"  # 60% of revenue
)

# Create a model
model = Model(
    line_items=[revenue, expenses],
    years=[2024, 2025, 2026]
)

# Calculate results
results = model.calculate()
print(results.to_dataframe())
```

## Key Features

### 📊 **Financial Modeling**
- Create line items with explicit values or formulas
- Organize items into categories with automatic totals
- Support for complex financial calculations using numexpr

### 📈 **Interactive Charts**
- Built-in Plotly integration for data visualization
- Line charts, bar charts, and mixed chart types
- Cumulative change and percent change charts

### 📋 **Flexible Tables**
- Generate formatted tables for financial statements
- Export to Excel with styling and formatting
- Configurable row types and table structures

### 🔧 **Advanced Features**
- Constraint validation for model integrity
- YAML/JSON serialization for model persistence
- Debt and financing generators
- Rich HTML output for Jupyter notebooks

## Usage Examples

### Working with Formulas

```python
# Line items can reference other line items in formulas
profit = LineItem(
    name="profit",
    category="income", 
    formula="revenue - expenses"
)

# Support for complex expressions
margin = LineItem(
    name="margin",
    category="ratios",
    formula="profit / revenue",
    value_format="percent"
)
```

### Creating Categories

```python
from pyproforma import Category

# Categories automatically calculate totals
revenue_category = Category(
    name="revenue",
    label="Revenue Sources",
    include_total=True
)

model.add.category(revenue_category)
```

### Generating Reports

```python
# Create formatted tables
table = model.tables.generate_table([
    {"type": "category", "name": "income"},
    {"type": "line_item", "name": "revenue"},
    {"type": "line_item", "name": "expenses"},
    {"type": "total", "category": "income"}
])

# Export to Excel
table.to_excel("financial_report.xlsx")

# Create interactive charts
chart = model.charts.item("revenue", chart_type="line")
chart.show()
```

### Model Persistence

```python
# Save model to YAML
model.save_yaml("model.yaml")

# Load model from YAML
model = Model.load_yaml("model.yaml")
```

## Development

Install in development mode with testing dependencies:

```bash
pip install -e .[dev]
```

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=pyproforma
```

## Requirements

- Python 3.9+
- pandas >= 1.3.0
- openpyxl >= 3.0.0
- numexpr >= 2.7.0
- jinja2 >= 3.0.0
- plotly >= 5.0.0
- PyYAML >= 6.0.0

## License

MIT License - see LICENSE file for details.
