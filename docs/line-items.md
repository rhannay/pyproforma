# Line Items & Data Access

## Line item types

### `FixedLine`

Hardcoded values, one per period. The simplest line item — use it for revenue assumptions, headcount, or any input that you control directly.

```python
from pyproforma import FixedLine

revenue = FixedLine(
    values={2024: 500_000, 2025: 550_000, 2026: 605_000},
    label="Revenue",
    tags=["operating"],
)
```

You can also supply a `value_format` to control how numbers appear in tables and charts:

```python
from pyproforma import Format

revenue = FixedLine(
    values={2024: 500_000, 2025: 550_000},
    label="Revenue",
    value_format=Format.CURRENCY_NO_DECIMALS,
)
```

### `FormulaLine`

Calculated from other line items or assumptions. The formula is a lambda that receives a unified namespace `li` and the current period `t`:

```python
from pyproforma import FormulaLine

gross_profit = FormulaLine(
    formula=lambda li, t: li.revenue[t] - li.cogs[t],
    label="Gross Profit",
)
```

### `Assumption`

A scalar constant — not period-specific. Accessed in formulas as a plain attribute (no `[t]`):

```python
from pyproforma import Assumption

tax_rate = Assumption(value=0.21, label="Tax Rate")

# In a formula:
net_income = FormulaLine(
    formula=lambda li, t: li.ebit[t] * (1 - li.tax_rate),
    label="Net Income",
)
```

### `InputLine`

Like `FixedLine` but the period values are supplied at instantiation:

```python
from pyproforma import InputLine

class Model(ProformaModel):
    revenue = InputLine(label="Revenue")

model = Model(periods=[2024, 2025], revenue={2024: 500_000, 2025: 550_000})
```

### Debt lines

`create_debt_lines` generates a pair of `DebtPrincipalLine` and `DebtInterestLine` from loan parameters:

```python
from pyproforma import create_debt_lines

principal, interest = create_debt_lines(
    name_prefix="loan",
    principal=1_000_000,
    rate=0.06,
    term=5,
    start_period=2024,
)
```

---

## The formula namespace

Every formula receives two arguments: `li` and `t`.

- **`t`** — the current period (an `int`, e.g. `2024`)
- **`li`** — a unified namespace giving access to both line items and assumptions

```python
formula=lambda li, t: ...
```

### Accessing line items

Line items are period-indexed — always pass `[t]`:

```python
formula=lambda li, t: li.revenue[t] * 0.55
formula=lambda li, t: li.revenue[t] - li.cogs[t]
```

### Accessing assumptions

Assumptions are scalars — no `[t]`:

```python
formula=lambda li, t: li.ebit[t] * (1 - li.tax_rate)
```

### Prior-period references

Use `t-1` to reference the previous period. Add a seed value on the `FixedLine` or `FormulaLine` itself to provide the base year:

```python
revenue = FormulaLine(
    formula=lambda li, t: li.revenue[t-1] * (1 + li.growth_rate),
    values={2024: 500_000},   # seed: used as the t-1 value for 2025
    label="Revenue",
)
```

### Tag sums in formulas

`li.tag["name"][t]` returns the sum of all line items tagged `"name"` for period `t`:

```python
total_operating = FormulaLine(
    formula=lambda li, t: li.tag["operating"][t],
    label="Total Operating Income",
)
```

---

## Tags

Tags let you group line items flexibly without fixed categories. A line item can have multiple tags.

```python
revenue = FixedLine(values={...}, tags=["revenue", "operating"])
other_income = FixedLine(values={...}, tags=["revenue"])
```

Access a tag group from the model:

```python
model.tag["revenue"]           # → LineItemSelection
model.tag["revenue"].names     # → ["revenue", "other_income"]
model.tag["revenue"].sum(2024) # → sum for period 2024
```

Tags are also usable in table row types — see [Tables](tables.md).

---

## Accessing data from an instantiated model

### Subscript access

```python
result = model["revenue"]        # → LineItemResult
result[2024]                     # → 500000.0
result.value(2024)               # same thing
result.values                    # → {2024: 500000.0, 2025: 550000.0, ...}
result.label                     # → "Revenue"
result.tags                      # → ["operating"]
result.value_format              # → NumberFormatSpec(...)
```

For assumptions:

```python
result = model["tax_rate"]       # → AssumptionResult
result.value                     # → 0.21
```

### Direct namespace access

`model.li` and `model.av` give lower-level access without creating result wrapper objects:

```python
model.li.revenue[2024]    # → 500000.0  (LineItemValues namespace)
model.av.tax_rate         # → 0.21      (AssumptionValues namespace)
```

### Convenience shortcuts

```python
model["revenue"].table()   # generate a table for this item
model["revenue"].chart()   # generate a chart for this item
```

---

## Value formatting

Every line item has a `value_format` (`NumberFormatSpec`). When not specified it defaults to `Format.NO_DECIMALS`. Formats flow through to tables and chart y-axis labels automatically.

| Format constant | Example output |
|---|---|
| `Format.NO_DECIMALS` | `500,000` |
| `Format.TWO_DECIMALS` | `500,000.00` |
| `Format.CURRENCY` | `$500,000.00` |
| `Format.CURRENCY_NO_DECIMALS` | `$500,000` |
| `Format.PERCENT` | `21%` |
| `Format.PERCENT_ONE_DECIMAL` | `21.0%` |
| `Format.PERCENT_TWO_DECIMALS` | `21.00%` |
| `Format.THOUSANDS` | `500` *(value divided by 1,000)* |
| `Format.MILLIONS` | `0.5` *(value divided by 1,000,000)* |
| `Format.THOUSANDS_K` | `500K` |
| `Format.MILLIONS_M` | `0.5M` |

For custom formats, use `NumberFormatSpec` directly:

```python
from pyproforma import NumberFormatSpec

fmt = NumberFormatSpec(decimals=1, scale="millions", suffix="M", thousands=False)
# 1_500_000 → "1.5M"
```

`NumberFormatSpec` parameters: `decimals`, `thousands` (bool), `prefix`, `suffix`, `multiplier`, `scale` (`"thousands"` or `"millions"`).
