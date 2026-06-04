# pyproforma

A Python library for building financial models — a code-first alternative to Excel for pro formas, projections, and structured financial tables.

```bash
pip install pyproforma
```

---

## Why

Spreadsheets are the default tool for financial modeling, but they have real problems: no version control, no testing, formulas hidden inside cells, and no easy way to generate the same model for multiple scenarios.

pyproforma is designed for analysts who want the benefits of code — reproducibility, testability, version history — without giving up the tabular output that finance people actually use.

---

## Quick example

```python
from pyproforma import ProformaModel, FixedLine, FormulaLine, Assumption

class IncomeStatement(ProformaModel):
    tax_rate = Assumption(value=0.21, label="Tax Rate")

    revenue = FixedLine(
        values={2024: 500_000, 2025: 550_000, 2026: 605_000},
        label="Revenue",
    )
    cogs = FormulaLine(
        formula=lambda li, t: li.revenue[t] * 0.55,
        label="Cost of Goods Sold",
    )
    gross_profit = FormulaLine(
        formula=lambda li, t: li.revenue[t] - li.cogs[t],
        label="Gross Profit",
    )
    net_income = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] * (1 - li.tax_rate),
        label="Net Income",
    )

model = IncomeStatement(periods=[2024, 2025, 2026])

model["net_income"][2024]          # → 178_425.0
model.tables.line_items().show()   # renders a table in Jupyter
model.charts.line_item("net_income").show()  # renders a chart
```

---

## What's in this documentation

<div class="grid cards" markdown>

- **[Getting Started](getting-started.md)**

    Install, define your first model, and get data out of it in five minutes.

- **[Line Items & Data Access](line-items.md)**

    All line item types, the formula namespace, assumptions, tags, and how to read values from an instantiated model.

- **[Tables](tables.md)**

    Generate formatted tables, use row templates, and export to HTML, Excel, or a DataFrame.

- **[Charts](charts.md)**

    Plot line items with matplotlib. The chart system is designed to also power future web output.

</div>
