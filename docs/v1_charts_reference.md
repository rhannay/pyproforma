# V1 Charts — Reference for Future V2 Implementation

This document captures how v1 charts worked so they can be recreated in v2.
The v1 chart code has been deleted; this is the authoritative reference.

---

## Architecture

Two layers:

1. **`Chart` / `ChartDataSet`** (`chart_class.py`) — a standalone, model-agnostic
   data structure that holds chart configuration and renders to Plotly. No dependency
   on the model.

2. **`Charts` namespace** (`charts.py`) — a model-aware helper (like v2's `Tables`)
   that pulls data out of the v1 model and constructs `Chart` objects. Accessed via
   `model.charts`.

This two-layer separation is worth keeping in v2: `Chart`/`ChartDataSet` stay
generic; a `Charts` namespace on `ProformaModel` handles the model integration.

---

## `ChartDataSet`

```python
ChartDataSet(
    label: str,                        # Legend label
    data: list[float | None],          # One value per period
    color: str | None = None,          # CSS color; auto-assigned if None
    type: "line"|"bar"|"scatter"|"pie" = "line",
    dashed: bool = False,              # Dashed line style (line type only)
)
```

Colors are auto-assigned from Plotly's qualitative palette
(`plotly.express.colors.qualitative.Plotly`) for any dataset where `color=None`.

Pie charts cannot be mixed with other types or used with multiple datasets —
validated at construction time.

---

## `Chart`

```python
Chart(
    labels: list[str],                 # X-axis labels (period labels, e.g. ["2024", "2025"])
    data_sets: list[ChartDataSet],
    id: str = "chart",                 # Unused in rendering, kept for identification
    title: str = "Chart",
    value_format: str | None = None,   # Y-axis format (see below)
)
```

### `chart.to_plotly(width, height, show_legend, template) -> go.Figure`

Renders to a `plotly.graph_objects.Figure`. Uses `go.Figure()` with individual
traces added per dataset type:

- `"bar"` → `go.Bar`
- `"line"` → `go.Scatter(mode="lines+markers")` with `line.dash="dash"` if dashed
- `"scatter"` → `go.Scatter(mode="markers")`
- `"pie"` → `go.Pie` (uses `chart.labels` as pie slice labels, not x-axis)

X-axis uses integer positions (`range(len(labels))`) with `tickvals`/`ticktext`
overriding the display to show the period labels. This makes mixed bar+line charts
align correctly.

**Y-axis formatting** via `value_format` string (maps to Plotly `tickformat`):
- `"no_decimals"` → `",.0f"`
- `"two_decimals"` → `",.2f"`
- `"percent"` → `".0%"`
- `"percent_one_decimal"` → `".1%"`
- `"percent_two_decimals"` → `".2%"`

Note: in v2, `value_format` should accept a `NumberFormatSpec` or `Format` constant
rather than a raw string, for consistency with the rest of the framework.

Layout defaults: `template="plotly_white"`, `hovermode="x unified"`, title centered.

---

## `Charts` Namespace (model integration)

Accessed as `model.charts`. Methods all return `go.Figure`.

### `charts.line_item(name, title, width, height, template, chart_type)`

Single line item over all periods. Pulls `label` and `value_format` from the model,
fetches values period by period, creates one `ChartDataSet`.

### `charts.line_items(item_names, title, width, height, template, value_format)`

Multiple line items as separate line traces. If `item_names=None`, uses all line
items. `value_format` defaults to the first item's format if not provided.

### `charts.cumulative_percent_change(item_names, width, height, template, start_year)`

Calls `model.line_item(name).cumulative_percent_change(year, start_year=start_year)`
for each period. `start_year` defaults to the first period. First period value is
`0.0` (no change). Y-axis formatted as percent.

### `charts.cumulative_change(item_names, width, height, template, start_year)`

Same pattern but absolute change. Calls
`model.line_item(name).cumulative_change(year, start_year=start_year)`.
Y-axis formatted as currency.

### `charts.index_to_year(item_names, width, height, template, start_year)`

Calls `model.line_item(name).index_to_year(year, start_year=start_year)`.
Base year = 100, other years indexed from there. Returns `None` when base value
is zero.

### `charts.line_items_pie(item_names, year, width, height, template)`

Pie chart of multiple line items at a single period. Defaults to the latest
period. Only includes items with positive values (skips zeros/negatives silently).

### `charts.constraint(constraint_name, width, height, template, line_item_type, constraint_type)`

Overlays a line item's values against a constraint's target values. Two datasets:
the line item (default `"bar"`) and the constraint target (default `"line"`).
This is v1-specific — v2 doesn't have constraints, so this method probably
won't be ported directly.

---

## V2 Implementation Notes

Key differences to account for when implementing in v2:

- **`model.years`** → **`model.periods`** in v2
- **`model.value(name, year)`** → **`model.li.{name}[t]`** or `model[name][t]`
- **`model.line_item(name).label`** → **`model[name].label`**
- **`model.line_item(name).value_format`** → **`model[name].value_format`**
- **`model.line_item_names`** → same in v2
- The `cumulative_percent_change`, `cumulative_change`, and `index_to_year`
  calculations need to be implemented on v2's `LineItemResult` (v1 had these
  as methods on its `LineItem` result object)
- The `constraint` chart has no v2 equivalent and can be skipped

The `Chart` / `ChartDataSet` classes are model-agnostic and can be moved directly
into v2 with one change: `value_format` should accept `NumberFormatSpec` / `Format`
constants in addition to strings.
