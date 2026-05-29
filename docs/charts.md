# Charts

pyproforma includes a chart system built on matplotlib. It uses a two-layer design: a backend-agnostic data layer (`ChartSpec`) and swappable rendering backends. Today the only backend is matplotlib; the same `ChartSpec` will power future web output (e.g. Chart.js) without changing how you build charts.

---

## The `model.charts` namespace

### Single line item

```python
# Line chart (default)
model.charts.line_item("revenue").show()

# Bar chart
model.charts.line_item("revenue", chart_type="bar").show()

# Custom title
model.charts.line_item("revenue", title="Annual Revenue").show()
```

### Multiple line items

Each named item becomes a separate series:

```python
model.charts.line_items(["revenue", "gross_profit", "net_income"]).show()

model.charts.line_items(
    ["cogs", "operating_expenses"],
    chart_type="bar",
    title="Cost Breakdown",
).show()

model.charts.line_items(
    ["cogs", "operating_expenses", "tax_expense"],
    chart_type="stacked_bar",
    title="Cost Stack",
).show()
```

### Convenience shortcut from `LineItemResult`

```python
model["net_income"].chart().show()
model["net_income"].chart(chart_type="bar").show()
```

---

## Chart types

| `chart_type` | Description |
|---|---|
| `"line"` | Time-series line chart with point markers (default) |
| `"bar"` | Grouped bar chart — one bar group per period, one bar per series |
| `"stacked_bar"` | Stacked bar chart — series stacked vertically |

---

## Y-axis formatting

The chart renderer reads the line item's `value_format` and applies it to the y-axis tick labels automatically. No extra configuration needed.

```python
from pyproforma import FixedLine, Format

revenue = FixedLine(
    values={2024: 1_000_000, 2025: 1_200_000},
    label="Revenue",
    value_format=Format.CURRENCY_NO_DECIMALS,  # y-axis shows "$1,000,000"
)

margin = FormulaLine(
    formula=lambda li, t: li.gross_profit[t] / li.revenue[t],
    label="Gross Margin",
    value_format=Format.PERCENT_ONE_DECIMAL,   # y-axis shows "60.0%"
)
```

---

## Working with the Figure object

`.figure()` returns a `matplotlib.figure.Figure` so you can customise it further or save it to disk:

```python
import matplotlib.pyplot as plt

fig = model.charts.line_item("net_income", title="Net Income Projection").figure(figsize=(12, 5))

ax = fig.axes[0]
ax.axhline(y=100_000, color="red", linestyle="--", label="Target")
ax.legend()

plt.show()

# Save to file
fig.savefig("net_income.png", dpi=150, bbox_inches="tight")
```

`figsize` defaults to `(10, 6)` — pass any tuple to override.

---

## The data layer: `ChartSpec`

`model.charts.line_item()` and `model.charts.line_items()` both return a `ChartSpec` — a plain Python object containing all the chart data with no matplotlib dependency. You can inspect or serialise it directly:

```python
spec = model.charts.line_item("revenue")

spec.chart_type    # → "line"
spec.title         # → "Revenue"
spec.series        # → [ChartSeries(label="Revenue", x_values=[...], y_values=[...])]
spec.value_format  # → NumberFormatSpec(...)

# Serialise to a plain dict (JSON-ready)
import json
print(json.dumps(spec.to_dict(), indent=2))
```

`to_dict()` output:

```json
{
  "chart_type": "line",
  "title": "Revenue",
  "x_label": null,
  "y_label": null,
  "series": [
    {
      "label": "Revenue",
      "x_values": [2024, 2025, 2026],
      "y_values": [500000.0, 550000.0, 605000.0],
      "color": null
    }
  ],
  "value_format": {
    "decimals": 0,
    "thousands": true,
    "prefix": "$",
    "suffix": "",
    "multiplier": 1.0,
    "scale": null
  }
}
```

This dict is what a future Chart.js or Plotly renderer would consume — the `ChartSpec` stays the same regardless of which backend renders it.

---

## `ChartSpec` methods summary

| Method | Description |
|---|---|
| `.show(figsize=(10, 6))` | Render and display via matplotlib (inline in Jupyter, window in a script) |
| `.figure(figsize=(10, 6))` | Return `matplotlib.figure.Figure` for further customisation |
| `.to_dict()` | Serialise to a plain dict — use with `json.dumps()` for web output |
