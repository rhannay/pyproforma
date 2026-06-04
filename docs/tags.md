# Tags

Tags let you group line items along any dimension you choose — revenue streams, cost categories, business units, whatever makes sense for your model. Unlike a rigid category hierarchy, a single line item can carry multiple tags, and tags can be summed in formulas or used to filter table output.

---

## Declaring tags

Pass a list of strings to the `tags` parameter of any line item:

```python
from pyproforma import ProformaModel, FixedLine, FormulaLine, Format

class BusinessModel(ProformaModel):
    product_revenue = FixedLine(
        values={2024: 400_000, 2025: 460_000, 2026: 529_000},
        label="Product Revenue",
        tags=["revenue"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    service_revenue = FixedLine(
        values={2024: 100_000, 2025: 115_000, 2026: 132_000},
        label="Service Revenue",
        tags=["revenue"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    cogs = FormulaLine(
        formula=lambda li, t: li.tag["revenue"][t] * 0.45,
        label="Cost of Goods Sold",
        tags=["opex"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    labor = FixedLine(
        values={2024: 120_000, 2025: 128_000, 2026: 136_000},
        label="Labor",
        tags=["opex"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    marketing = FixedLine(
        values={2024: 40_000, 2025: 45_000, 2026: 50_000},
        label="Marketing",
        tags=["opex"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    total_revenue = FormulaLine(
        formula=lambda li, t: li.tag["revenue"][t],
        label="Total Revenue",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    total_opex = FormulaLine(
        formula=lambda li, t: li.tag["opex"][t],
        label="Total Operating Expenses",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    operating_profit = FormulaLine(
        formula=lambda li, t: li.total_revenue[t] - li.total_opex[t],
        label="Operating Profit",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

model = BusinessModel(periods=[2024, 2025, 2026])
```

A line item can have any number of tags:

```python
cost_of_goods_sold = FixedLine(
    values={...},
    tags=["opex", "variable_cost", "cogs"],
)
```

---

## Using tags in formulas

Inside a formula, `li.tag["name"][t]` returns the **sum of all line items carrying that tag** for period `t`. This is the most common use of tags — it means you can add a new revenue stream just by tagging it, without touching the formula that totals revenue.

```python
# Automatically includes any line item tagged "revenue"
total_revenue = FormulaLine(
    formula=lambda li, t: li.tag["revenue"][t],
    label="Total Revenue",
)

# Tags on the left side of a subtraction
operating_profit = FormulaLine(
    formula=lambda li, t: li.tag["revenue"][t] - li.tag["opex"][t],
    label="Operating Profit",
)
```

---

## Accessing tags after instantiation

`model.tag["name"]` returns a `LineItemSelection` — a lightweight object representing all line items that carry that tag.

```python
revenue_selection = model.tag["revenue"]

revenue_selection.names          # ["product_revenue", "service_revenue"]
revenue_selection.sum(2024)      # 500_000.0  (same as li.tag["revenue"][2024])
revenue_selection.value(2024)    # {"product_revenue": 400_000.0, "service_revenue": 100_000.0}
```

You can also check which tags a specific line item carries:

```python
model["product_revenue"].tags    # ["revenue"]
model["cogs"].tags               # ["opex"]
```

---

## Tags in tables

### `TagTotalRow`

Add a subtotal row for any tag using `TagTotalRow` in a `from_template` call:

```python
from pyproforma.tables import HeaderRow, LabelRow, ItemRow, BlankRow, TagTotalRow

table = model.tables.from_template([
    HeaderRow(),
    LabelRow(label="Revenue"),
    ItemRow(name="product_revenue"),
    ItemRow(name="service_revenue", bottom_border="single"),
    TagTotalRow(tag="revenue", label="Total Revenue", bold=True),
    BlankRow(),
    LabelRow(label="Operating Expenses"),
    ItemRow(name="cogs"),
    ItemRow(name="labor"),
    ItemRow(name="marketing", bottom_border="single"),
    TagTotalRow(tag="opex", label="Total OpEx", bold=True),
])
table.show()
```

The tag list is resolved at render time, so the total stays correct if you add or remove tagged items from the model.

### `LineItemSelection.table()`

Generate a table containing only the items with a given tag:

```python
model.tag["revenue"].table().show()
model.tag["opex"].table(include_label=True).show()
```
