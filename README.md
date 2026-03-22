# pyproforma

A Python library for building financial models — a code-first alternative to Excel for pro formas, projections, and structured financial tables.

```bash
pip install pyproforma
```

---

## Why

Spreadsheets are the default tool for financial modeling, but they have real problems: no version control, no testing, formulas hidden inside cells, and no easy way to generate the same model for multiple scenarios. pyproforma is designed for analysts who want the benefits of code — reproducibility, testability, version history — without giving up the tabular output that finance people actually use.

---

## How it works

Define a model by subclassing `ProformaModel` and declaring line items as class attributes. Instantiate it with a list of periods and the library calculates everything.

```python
from pyproforma import ProformaModel, FixedLine, FormulaLine, Assumption

class IncomeStatement(ProformaModel):
    growth_rate = Assumption(value=0.10)

    revenue = FixedLine(
        values={2024: 500_000, 2025: 550_000, 2026: 605_000},
        label="Revenue",
        tags=["operating"],
    )
    cogs = FormulaLine(
        formula=lambda li, t: li.revenue[t] * 0.55,
        label="Cost of Goods Sold",
        tags=["operating"],
    )
    gross_profit = FormulaLine(
        formula=lambda li, t: li.revenue[t] - li.cogs[t],
        label="Gross Profit",
    )
    tax_expense = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] * 0.21,
        label="Tax Expense",
    )
    net_income = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] - li.tax_expense[t],
        label="Net Income",
    )

model = IncomeStatement(periods=[2024, 2025, 2026])
```

Access results directly:

```python
model["net_income"][2025]   # 218_130.0
model["gross_profit"][2024] # 225_000.0
```

---

## Tables

Generate formatted tables for display or export. Tables are the primary output — they render to HTML (for Jupyter notebooks), Excel, or a pandas DataFrame.

```python
# All line items
model.tables.line_items().show()

# Single item with period-over-period analysis
model.tables.line_item("net_income", include_percent_change=True).show()

# Show what feeds into a calculated line item
model.tables.precedents("net_income").show()

# Custom layout using a template
from pyproforma import Format
from pyproforma.tables import HeaderRow, LabelRow, ItemRow

table = model.tables.from_template([
    HeaderRow(),
    LabelRow(label="Income Statement"),
    ItemRow(name="revenue", value_format=Format.THOUSANDS_K),
    ItemRow(name="cogs",    value_format=Format.THOUSANDS_K, bottom_border="single"),
    ItemRow(name="gross_profit", bold=True, value_format=Format.THOUSANDS_K),
])
table.show()
```

Export to Excel with formatting preserved:

```python
model.tables.line_items().to_excel("income_statement.xlsx")
```

---

## Scenarios and comparisons

A model is just a class — create multiple instances with different inputs to compare scenarios.

```python
class FlexModel(ProformaModel):
    cogs_rate = Assumption(value=0.55)
    revenue = FixedLine(values={2024: 500_000, 2025: 550_000})
    cogs = FormulaLine(formula=lambda li, t: li.revenue[t] * li.cogs_rate)
    gross_profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.cogs[t])

base = FlexModel(periods=[2024, 2025])
# InputAssumption lets callers override at instantiation time — coming soon
```

Use `ModelComparison` to diff two model instances:

```python
from pyproforma import ModelComparison

# (requires two separately instantiated models with different inputs)
comparison = ModelComparison(base, upside)
comparison.diff("gross_profit")
```

---

## Time-series formulas

Formulas receive the full model namespace and the current period `t`. Reference prior periods with `t-1`:

```python
# Compound growth from a seeded base year
revenue = FormulaLine(
    formula=lambda li, t: li.revenue[t-1] * (1 + li.growth_rate),
    values={2024: 500_000},  # seed value for first period
    label="Revenue",
)
```

---

## Tags

Tag line items to group them flexibly without fixed categories:

```python
revenue = FixedLine(values={...}, tags=["operating", "top_line"])
other_income = FixedLine(values={...}, tags=["operating"])

# Sum all items tagged "operating" in a formula
ebit = FormulaLine(formula=lambda li, t: li.tag["operating"][t])

# Or in a table
from pyproforma.tables import TagTotalRow
table = model.tables.from_template([
    HeaderRow(),
    ItemRow(name="revenue"),
    ItemRow(name="other_income"),
    TagTotalRow(tag="operating", label="Total Operating"),
])
```

---

## Number formatting

A `Format` class provides named format constants that flow through to both HTML and Excel output:

```python
from pyproforma import Format

ItemRow(name="revenue",    value_format=Format.THOUSANDS_K)   # 500K
ItemRow(name="margin",     value_format=Format.PERCENT_ONE_DECIMAL)  # 45.0%
ItemRow(name="net_income", value_format=Format.CURRENCY_NO_DECIMALS) # $218,130
```

Custom formats via `NumberFormatSpec`:

```python
from pyproforma import NumberFormatSpec

fmt = NumberFormatSpec(decimals=1, scale="millions", suffix="M")
# 500_000 → "0.5M"
```

---

## Installation

```bash
pip install pyproforma
```

Requires Python 3.9+. Dependencies: pandas, openpyxl.

---

## Status

This project is in active development. The core modeling and table export features are stable. Charts, extended documentation, and additional row types are on the roadmap. Feedback welcome — open an issue or reach out directly.

## License

MIT
