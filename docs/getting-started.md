# Getting Started

## Installation

```bash
pip install pyproforma
```

Requires Python 3.9+.

---

## Your first model

A model is a Python class. Subclass `ProformaModel` and declare line items as class attributes.

```python
from pyproforma import ProformaModel, FixedLine, FormulaLine, Assumption

class CoffeeShop(ProformaModel):
    # A scalar constant — not period-specific
    cogs_rate = Assumption(value=0.40, label="COGS Rate")

    # Fixed values supplied per period
    revenue = FixedLine(
        values={2024: 120_000, 2025: 138_000, 2026: 158_000},
        label="Revenue",
    )

    # Calculated from other line items
    cogs = FormulaLine(
        formula=lambda li, t: li.revenue[t] * li.cogs_rate,
        label="Cost of Goods Sold",
    )
    gross_profit = FormulaLine(
        formula=lambda li, t: li.revenue[t] - li.cogs[t],
        label="Gross Profit",
    )
    operating_expenses = FixedLine(
        values={2024: 40_000, 2025: 43_000, 2026: 47_000},
        label="Operating Expenses",
    )
    net_income = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] - li.operating_expenses[t],
        label="Net Income",
    )
```

Instantiate it with a list of periods:

```python
model = CoffeeShop(periods=[2024, 2025, 2026])
```

Everything is calculated immediately on instantiation. Declaration order doesn't matter — the engine resolves dependencies automatically.

---

## Getting values out

```python
# Subscript access: model["name"][period]
model["revenue"][2024]       # → 120000.0
model["net_income"][2025]    # → 38600.0

# All periods at once
model["revenue"].values      # → {2024: 120000.0, 2025: 138000.0, 2026: 158000.0}

# Assumption value
model["cogs_rate"].value     # → 0.4

# List all line items and scalars
model.line_item_names        # → ["revenue", "cogs", "gross_profit", ...]
model.scalar_names           # → ["cogs_rate"]
```

---

## Displaying a table

```python
# All line items in the model
model.tables.line_items().show()

# Single item
model["net_income"].table().show()

# Single item with period-over-period % change
model["revenue"].table(include_percent_change=True).show()
```

In Jupyter the table renders as styled HTML. Outside Jupyter, use `.to_html()` to get the HTML string.

---

## Displaying a chart

```python
model.charts.line_item("net_income").show()

model.charts.line_items(["revenue", "gross_profit", "net_income"]).show()
```

---

## Next steps

- **[Line Items & Data Access](line-items.md)** — learn about all line item types, the formula namespace, and tags
- **[Tables](tables.md)** — custom templates, row types, and export options
- **[Charts](charts.md)** — chart types and the two-layer chart architecture
