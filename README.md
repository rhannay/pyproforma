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
from pyproforma import ProformaModel, FixedLine, FormulaLine, ScalarLine, Format

class IncomeStatement(ProformaModel):
    default_periods = [2024, 2025, 2026]

    tax_rate = ScalarLine(value=0.21, label="Tax Rate")

    revenue = FixedLine(
        values={2024: 500_000, 2025: 550_000, 2026: 605_000},
        label="Revenue",
        tags=["operating"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    cogs = FormulaLine(
        formula=lambda li, t: li.revenue[t] * 0.55,
        label="Cost of Goods Sold",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    gross_profit = FormulaLine(
        formula=lambda li, t: li.revenue[t] - li.cogs[t],
        label="Gross Profit",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    net_income = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] * (1 - li.tax_rate),
        label="Net Income",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

model = IncomeStatement()  # uses default_periods
```

Access results with dot notation (primary) or bracket notation (useful when the name is in a variable):

```python
model.net_income[2025]      # 173_745.0  — dot notation
model["net_income"][2025]   # same value — bracket notation

model.tax_rate.value        # 0.21  — scalars have .value, not [t]

model.periods               # [2024, 2025, 2026]
model.line_item_names       # ["revenue", "cogs", "gross_profit", "net_income"]
model.scalar_names          # ["tax_rate"]
```

---

## Line item types

| Type | Use |
|------|-----|
| `FixedLine(values, ...)` | Hardcoded values per period |
| `FormulaLine(formula, ...)` | Calculated from other items via a lambda |
| `ScalarLine(value, ...)` | A single value shared across all periods |
| `InputLine(default, ...)` | Period-indexed values supplied at instantiation |
| `ScalarInputLine(default, ...)` | A single value supplied at instantiation |

Formula lambdas receive `li` (the model namespace) and `t` (the current period). Period-indexed items use `li.name[t]`; scalars use `li.name` (no `[t]`). Reference prior periods with `li.name[t-1]`.

---

## Scenario inputs

`InputLine` and `ScalarInputLine` let callers supply values at instantiation without subclassing again — useful for scenario analysis.

```python
from pyproforma import InputLine, ScalarInputLine

class FlexModel(ProformaModel):
    default_periods = [2024, 2025, 2026]

    margin = ScalarInputLine(default=0.45, label="Gross Margin")
    revenue = FixedLine(
        values={2024: 500_000, 2025: 550_000, 2026: 605_000},
        label="Revenue",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    gross_profit = FormulaLine(
        formula=lambda li, t: li.revenue[t] * li.margin,
        label="Gross Profit",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

base   = FlexModel()                  # uses default margin of 0.45
upside = FlexModel(margin=0.52)       # override at instantiation
```

Use `model.compare()` to diff two instances:

```python
comparison = base.compare(upside, labels=["Base", "Upside"])
```

---

## Time-series formulas

Seed a value in the first period and let the formula compound from there — no `if t == first_year` guards needed:

```python
revenue = FormulaLine(
    formula=lambda li, t: li.revenue[t-1] * (1 + li.growth_rate),
    values={2024: 500_000},   # engine uses this for 2024; formula runs from 2025 onward
    label="Revenue",
)
```

---

## Tags

Tag line items to group them without fixed categories:

```python
water_sales = FixedLine(values={...}, tags=["revenue"])
power_sales = FixedLine(values={...}, tags=["revenue"])

# Sum all "revenue"-tagged items in a formula
total_revenue = FormulaLine(formula=lambda li, t: li.tag["revenue"][t])
```

Tags also work in table templates:

```python
from pyproforma import TagTotalRow
TagTotalRow(tag="revenue", label="Total Revenue")
```

---

## Tables

Generate formatted tables for HTML, Excel, or pandas. `from_template` gives full control over layout:

```python
from pyproforma import HeaderRow, LabelRow, ItemRow, BlankRow, LineItemsTotalRow

table = model.tables.from_template([
    HeaderRow(),
    LabelRow("Income Statement"),
    ItemRow("revenue"),
    ItemRow("cogs", reverse_sign=True),   # display as positive deduction
    ItemRow("gross_profit", bold=True, borders="top"),
    BlankRow(),
    ItemRow("net_income", bold=True),
])

table.show()                           # inline in Jupyter
table.to_excel("output.xlsx")          # Excel with formatting preserved
table.to_dataframe()                   # pandas DataFrame
```

Convenience builders for common layouts:

```python
model.tables.line_items().show()                              # all line items
model.tables.line_item("net_income", include_percent_change=True).show()
model.tables.precedents("net_income").show()                  # formula dependency tree
```

---

## Charts

```python
model.charts.line_item("net_income", chart_type="bar").show()
model.charts.line_items(["revenue", "gross_profit", "net_income"]).show()
```

Charts return a `ChartSpec` which can also render to a matplotlib `Figure`:

```python
fig = model.charts.line_item("net_income").figure()
```

Requires `pip install pyproforma[charts]`.

---

## Number formatting

Named format constants flow through to both HTML and Excel output:

```python
from pyproforma import Format

ItemRow("revenue",    value_format=Format.CURRENCY_NO_DECIMALS)  # $500,000
ItemRow("revenue",    value_format=Format.THOUSANDS_K)           # 500.0K
ItemRow("margin",     value_format=Format.PERCENT_ONE_DECIMAL)   # 45.0%
ItemRow("net_income", value_format=Format.MILLIONS_M)            # $0.2M
```

Custom formats via `NumberFormatSpec`:

```python
from pyproforma import NumberFormatSpec

fmt = NumberFormatSpec(decimals=1, scale="millions", prefix="$", suffix="M")
# 500_000 → "$0.5M"
```

---

## Explorer

A lightweight Flask web app for browsing any model interactively:

```python
from pyproforma.explorer import create_app

app = create_app(model)
app.run(debug=True)
```

Requires `pip install pyproforma[explorer]`. The app shows all line items, their values, formula sources, and lets you update `InputLine` / `ScalarInputLine` values live. You can also pass named tables, charts, and views to build a richer dashboard.

---

## Installation

```bash
pip install pyproforma                   # core only
pip install pyproforma[charts]           # + matplotlib
pip install pyproforma[excel]            # + openpyxl
pip install pyproforma[explorer]         # + Flask
pip install pyproforma[pandas]           # + pandas
```

Requires Python 3.9+.

---

## Status

Active development. Core modeling, table export, charts, and the Flask explorer are all stable. Feedback welcome — open an issue on GitHub.

## License

MIT
